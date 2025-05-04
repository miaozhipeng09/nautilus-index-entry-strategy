from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd

from nautilus_trader.core.message import Event
from nautilus_trader.model.data import Bar, BarType, BarSpecification, QuoteTick
from nautilus_trader.model.enums import OrderSide, PositionSide, PriceType, BarAggregation
from nautilus_trader.model.events import PositionOpened
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity, Price
from nautilus_trader.trading.strategy import Strategy

from config.dynamic_event_strategy_config import DynamicEventStrategyConfig
from models.event_loader import IndexEventLoader


class DynamicEventStrategy(Strategy):
    """
    Event-driven strategy for index constituent adjustment
    """

    def __init__(self, config: DynamicEventStrategyConfig):
        super().__init__(config)

        # Configuration parameters
        self.price_change_threshold = config.price_change_threshold
        self.trade_size = Quantity.from_int(config.trade_size)
        self.commission_per_share = config.commission_per_share
        self.max_position_ratio = config.max_position_ratio
        self.stop_loss = config.stop_loss
        self.take_profit = config.take_profit
        self.bar_spec = BarSpecification(1, BarAggregation.DAY, PriceType.LAST)

        # Event handling
        self.event_loader = IndexEventLoader(Path(config.event_file_path))
        self.instrument_events: Dict[str, List[Tuple[datetime, datetime]]] = {}
        self.active_events: Dict[str, datetime] = {}
        self.announcement_prices: Dict[str, float] = {}
        self.position_open_prices: Dict[str, float] = {}  # Record entry price for open positions

    def on_start(self):
        """Initialize strategy on start"""
        for instrument_id in self.config.instrument_ids:
            symbol = instrument_id.symbol.value
            events = self.event_loader.get_events_for_instrument(symbol)
            if events:
                self.instrument_events[symbol] = events
                bar_type = BarType(
                    instrument_id=instrument_id,
                    bar_spec=self.bar_spec
                )
                self.subscribe_bars(bar_type)
                self.log.info(f"Subscribed to {symbol} event trading opportunities, found {len(events)} events")

        self.log.info(f"Monitoring event opportunities for {len(self.instrument_events)} instruments")

    def on_bar(self, bar: Bar):
        instrument_id = bar.bar_type.instrument_id
        symbol = instrument_id.symbol.value
        current_date = pd.Timestamp(bar.ts_event, unit='ns').floor('D').to_pydatetime()

        # Check take-profit and stop-loss conditions
        self._check_profit_and_loss(instrument_id, bar)

        if symbol not in self.instrument_events:
            return

        for announce_date, trade_date in self.instrument_events[symbol]:
            if current_date == announce_date + timedelta(days=1):
                self._handle_announcement_day_after(bar, instrument_id, announce_date, trade_date)
            elif current_date == trade_date + timedelta(days=1):
                self._handle_trade_day_after(instrument_id)

    def _check_profit_and_loss(self, instrument_id: InstrumentId, bar: Bar):
        """Check take-profit and stop-loss conditions"""
        symbol = instrument_id.symbol.value
        positions = self.cache.positions(instrument_id=instrument_id)

        if not positions or symbol not in self.position_open_prices:
            return

        position = positions[0]
        current_price = bar.close.as_double()
        open_price = self.position_open_prices[symbol]
        current_pnl = (current_price - open_price) / open_price

        # Check take-profit
        if current_pnl >= self.take_profit:
            self.close_position(position)
            self.log.info(f"Take-profit exit for {symbol} (Profit {current_pnl:.2%} >= {self.take_profit:.2%})")
            self._cleanup_position_data(symbol)
            return

        # Check stop-loss
        if current_pnl <= -self.stop_loss:
            self.close_position(position)
            self.log.info(f"Stop-loss exit for {symbol} (Loss {current_pnl:.2%} <= -{self.stop_loss:.2%})")
            self._cleanup_position_data(symbol)

    def _cleanup_position_data(self, symbol: str):
        """Clean up data related to position"""
        if symbol in self.position_open_prices:
            del self.position_open_prices[symbol]
        if symbol in self.active_events:
            del self.active_events[symbol]

    def _handle_announcement_day_after(self, bar: Bar, instrument_id: InstrumentId,
                                       announce_date: datetime, trade_date: datetime):
        symbol = instrument_id.symbol.value
        announcement_close = bar.close.as_double()
        price_change = (bar.open.as_double() - announcement_close) / announcement_close

        if abs(price_change) > self.price_change_threshold:
            side = OrderSide.SELL if price_change > 0 else OrderSide.BUY
            self._submit_order(instrument_id, side, bar.close)
            self.active_events[symbol] = trade_date
            self.position_open_prices[symbol] = bar.close.as_double()
            self.log.info(f"{symbol} {side.name} signal (Price change {price_change:.2%})")

    def _handle_trade_day_after(self, instrument_id: InstrumentId):
        symbol = instrument_id.symbol.value
        positions = self.cache.positions(instrument_id=instrument_id)
        if positions:
            position = positions[0]
            self.close_position(position)
            self.log.info(f"Exit position for {symbol} (Day after index adjustment)")
            self._cleanup_position_data(symbol)

    def _submit_order(self, instrument_id: InstrumentId, side: OrderSide, current_price: Price = None):
        quantity = self._calculate_position_size(instrument_id, side, current_price)
        if quantity == 0:
            self.log.warning("Calculated trade size is 0, skipping order")
            return

        order = self.order_factory.market(
            instrument_id=instrument_id,
            order_side=side,
            quantity=quantity,
        )
        self.submit_order(order)

    def _calculate_position_size(self, instrument_id: InstrumentId, side: OrderSide,
                                 current_price: Price = None) -> Quantity:
        account = self.cache.account_for_venue(instrument_id.venue)
        if not account:
            self.log.warning(f"Account not found for venue {instrument_id.venue}")
            return Quantity.zero()

        free_balance = account.balance().free.as_decimal()
        if free_balance <= 0:
            self.log.warning(f"Insufficient available funds: {free_balance}")
            return Quantity.zero()

        price = current_price
        if price is None:
            last_tick = self.cache.tick(instrument_id)
            if last_tick:
                price = last_tick.ask if side == OrderSide.BUY else last_tick.bid
            else:
                last_bar = self.cache.bar(instrument_id)
                if last_bar:
                    price = last_bar.close

        if not price or price.as_decimal() <= 0:
            self.log.warning("Unable to obtain valid price")
            return Quantity.zero()

        max_position_value = free_balance * Decimal(str(self.max_position_ratio))
        size = max_position_value / price.as_decimal()
        trade_size = int(self.trade_size.as_double())
        return Quantity.from_int(min(int(size), trade_size))

    def on_stop(self):
        """Clean up all positions on strategy stop (close one by one)"""
        try:
            open_positions = list(self.cache.positions_open())  # Get all open positions
            if not open_positions:
                self.log.info("Strategy stopped: no positions to clean up")
                return

            self.log.info(f"Starting cleanup of {len(open_positions)} positions...")
            for position in open_positions:
                self.close_position(position)
                self.log.info(f"Sent close instruction: {position}")

            self.log.info("All position close instructions sent")
        except Exception as e:
            self.log.error(f"Error occurred during position cleanup: {str(e)}", exc_info=True)
            raise  # Re-raise to ensure correct strategy state update

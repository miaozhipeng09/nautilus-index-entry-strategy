from nautilus_trader.trading.strategy import Strategy, StrategyConfig
from nautilus_trader.model import Quantity, QuoteTick, InstrumentId, Position
from nautilus_trader.indicators.macd import MovingAverageConvergenceDivergence
from nautilus_trader.model.enums import OrderSide, PositionSide, PriceType
from nautilus_trader.core.message import Event
from nautilus_trader.model.events import PositionOpened

class MACDConfig(StrategyConfig):
    instrument_id: InstrumentId
    fast_period: int = 12
    slow_period: int = 26
    trade_size: int = 1_000_000
    entry_threshold: float = 0.00010

class MACDStrategy(Strategy):
    def __init__(self, config: MACDConfig):
        super().__init__(config=config)
        self.macd = MovingAverageConvergenceDivergence(
            fast_period=config.fast_period,
            slow_period=config.slow_period,
            price_type=PriceType.MID,
        )
        self.trade_size = Quantity.from_int(config.trade_size)
        self.position: Position | None = None

    def on_start(self):
        self.subscribe_quote_ticks(self.config.instrument_id)

    def on_stop(self):
        self.close_all_positions(self.config.instrument_id)
        self.unsubscribe_quote_ticks(self.config.instrument_id)

    def on_quote_tick(self, tick: QuoteTick):
        self.macd.handle_quote_tick(tick)
        if not self.macd.initialized:
            return
        self.check_for_entry()
        self.check_for_exit()

    def on_event(self, event: Event):
        if isinstance(event, PositionOpened):
            self.position = self.cache.position(event.position_id)

    def check_for_entry(self):
        if self.macd.value > self.config.entry_threshold:
            if not self.position or self.position.side != PositionSide.LONG:
                order = self.order_factory.market(
                    self.config.instrument_id, OrderSide.BUY, self.trade_size
                )
                self.submit_order(order)
        elif self.macd.value < -self.config.entry_threshold:
            if not self.position or self.position.side != PositionSide.SHORT:
                order = self.order_factory.market(
                    self.config.instrument_id, OrderSide.SELL, self.trade_size
                )
                self.submit_order(order)

    def check_for_exit(self):
        if self.macd.value >= 0.0 and self.position and self.position.side == PositionSide.SHORT:
            self.close_position(self.position)
        elif self.macd.value < 0.0 and self.position and self.position.side == PositionSide.LONG:
            self.close_position(self.position)

    def on_dispose(self):
        pass

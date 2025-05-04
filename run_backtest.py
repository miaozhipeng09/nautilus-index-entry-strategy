# run_backtest.py
import pandas as pd
from pathlib import Path
from decimal import Decimal
from typing import Dict, List

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model import TraderId, Venue, Money
from nautilus_trader.model.objects import Currency, Price, Quantity
from nautilus_trader.model.enums import AccountType, OmsType, BarAggregation, PriceType
from nautilus_trader.model.identifiers import InstrumentId, Symbol
from nautilus_trader.model.data import Bar, BarSpecification, BarType
from nautilus_trader.model.instruments import Equity
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.config import LoggingConfig

from strategy.dynamic_event_strategy import DynamicEventStrategy
from config.dynamic_event_strategy_config import DynamicEventStrategyConfig


def load_and_convert_data(file_path: Path, instrument: Equity, bar_spec: BarSpecification) -> List[Bar]:
    """Load and convert candlestick data to Nautilus format"""
    try:
        df = pd.read_parquet(file_path)
        if df.empty:
            print(f"⚠️ Empty data file: {file_path}")
            return []

        # Data preprocessing
        df = (df[['open_time', 'open', 'high', 'low', 'close', 'volume']]
              .rename(columns={'open_time': 'timestamp'})
              .assign(timestamp=lambda x: pd.to_datetime(x['timestamp'], unit='ns'))
              .set_index('timestamp'))

        # Type conversion
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
        df['volume'] = df['volume'].fillna(0).astype(float)

        # Create Bar converter
        bar_type = BarType(
            instrument_id=instrument.id,
            bar_spec=bar_spec
        )

        wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
        return list(wrangler.process(df))

    except Exception as e:
        print(f"❌ Failed to load {file_path}: {e}")
        return []


def initialize_instruments(df: pd.DataFrame, venue: Venue) -> Dict[str, Equity]:
    """Initialize all trading instruments"""
    instruments = {}
    for _, row in df.iterrows():
        try:
            symbol = row["symbol"]
            inst_id = InstrumentId(symbol=Symbol(symbol), venue=venue)

            inst = Equity(
                instrument_id=inst_id,
                raw_symbol=Symbol(symbol),
                currency=Currency.from_str("USD"),
                price_precision=2,
                price_increment=Price(Decimal(str(row["tick_size"])), precision=2),
                lot_size=Quantity(Decimal(str(row["lot_size"])), precision=0),
                ts_event=0,
                ts_init=0,
                max_quantity=Quantity(Decimal(str(row["max_size"])), precision=0),
                min_quantity=Quantity(Decimal(str(row["min_size"])), precision=0),
                margin_init=Decimal(str(row.get("margin", 0))),
                margin_maint=Decimal(str(row.get("margin", 0))),
            )
            instruments[symbol] = inst
            print(f"✅ Successfully added {inst.id}")

        except Exception as e:
            print(f"❌ Failed to add {symbol}: {str(e)}")

    return instruments


def main():
    # 1. Path configuration
    base_dir = Path(__file__).parent
    catalog_path = base_dir / "parquet_catalog"
    output_dir = base_dir / "backtest_results"

    # 2. Load instrument metadata
    instruments_df = pd.read_parquet(catalog_path / "_instruments.parquet")
    print(f"✅ Loaded {len(instruments_df)} instruments")

    # 3. Define Bar specification
    bar_spec = BarSpecification(1, BarAggregation.DAY, PriceType.LAST)

    # 4. Initialize backtest engine
    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=TraderId("BACKTESTER-001"),
            logging=LoggingConfig(log_level="INFO")
        )
    )

    # 5. Add trading venue
    sim_venue = Venue("SIM")
    engine.add_venue(
        venue=sim_venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=Currency.from_str("USD"),
        starting_balances=[Money(5_000_000.0, Currency.from_str("USD"))],
    )

    # 6. Add all instruments
    instrument_map = initialize_instruments(instruments_df, sim_venue)
    for inst in instrument_map.values():
        engine.add_instrument(inst)

    # 7. Load candlestick data
    total_bars = 0
    for file in catalog_path.glob("*.parquet"):
        if file.name.startswith("_"):
            continue

        symbol = file.stem
        if symbol not in instrument_map:
            print(f"⚠️ Skipping unmatched instrument: {file.name}")
            continue

        bars = load_and_convert_data(file, instrument_map[symbol], bar_spec)
        if bars:
            engine.add_data(bars)
            total_bars += len(bars)
            print(f"✅ Loaded {len(bars)} bars: {symbol}")

    # 8. Add strategy
    strategy_cfg = DynamicEventStrategyConfig(
        instrument_ids=[inst.id for inst in instrument_map.values()],
        event_file_path=str(base_dir / "Index Add Event Data.xlsx"),
        price_change_threshold=0.01,
        trade_size=20000,
        commission_per_share=0.01,
        max_position_ratio=0.2
    )
    engine.add_strategy(DynamicEventStrategy(config=strategy_cfg))

    # 9. Run backtest
    print("🚀 Starting backtest...")
    engine.run()
    print("✅ Backtest complete!")

    # 10. Save results
    output_dir.mkdir(parents=True, exist_ok=True)

    engine.trader.generate_order_fills_report().to_csv(output_dir / "order_fills.csv")
    engine.trader.generate_positions_report().to_csv(output_dir / "positions.csv")
    engine.trader.generate_account_report(sim_venue).to_csv(output_dir / "account.csv")

    print(f"📊 Backtest results saved to {output_dir}")


if __name__ == "__main__":
    main()

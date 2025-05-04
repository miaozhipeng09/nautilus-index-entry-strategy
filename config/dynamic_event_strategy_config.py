from nautilus_trader.trading.strategy import StrategyConfig
from nautilus_trader.model.identifiers import InstrumentId
from typing import Sequence
from pathlib import Path
from decimal import Decimal


class DynamicEventStrategyConfig(StrategyConfig):
    # Instruments
    instrument_ids: Sequence[InstrumentId] = []

    # Strategy parameters
    event_file_path: str = "Index Add Event Data.xlsx"
    price_change_threshold: float = 0.01
    max_position_ratio: float = 0.1
    trade_size: int = 1000
    commission_per_share: float = 0.01
    stop_loss: float = 0.05
    take_profit: float = 0.03

    # Backtest parameters
    starting_balance: float = 5_000_000.0
    bar_interval: int = 1
    bar_aggregation: str = "DAY"
    bar_price_type: str = "LAST"

    # File paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    catalog_dir: str = "parquet_catalog"
    result_dir: str = "backtest_results"

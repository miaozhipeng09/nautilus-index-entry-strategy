from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.backtest.node import BacktestDataConfig
from nautilus_trader.model import QuoteTick

# 自动从环境变量或默认路径加载Parquet数据
from nautilus_trader.persistence.catalog import ParquetDataCatalog

catalog = ParquetDataCatalog("./data/catalog")  # 这里直接填相对路径，指向你的data/catalog
instruments = catalog.instruments()


# 只取第一个Instrument（比如EUR/USD）
data = BacktestDataConfig(
    catalog_path=str(catalog.path),
    data_cls=QuoteTick,
    instrument_id=instruments[0].id,
    end_time="2020-01-10",
)

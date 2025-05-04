from nautilus_trader.backtest.node import BacktestEngineConfig
from nautilus_trader.config import ImportableStrategyConfig, LoggingConfig

engine = BacktestEngineConfig(
    strategies=[
        ImportableStrategyConfig(
            strategy_path="strategies.macd_strategy:MACDStrategy",
            config_path="strategies.macd_strategy:MACDConfig",
            config={
                "instrument_id": "FX:EUR/USD",   # 实际运行时从data_config中动态传入更好
                "fast_period": 12,
                "slow_period": 26,
            },
        )
    ],
    logging=LoggingConfig(log_level="ERROR"),
)

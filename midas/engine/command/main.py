# main.py
import logging
from .config import Config, Mode
from .parameters import Parameters
from midas.engine.strategies import load_strategy_class
from .controller import LiveEventController, BacktestEventController

def run(mode: str, strategy_module: str, strategy_class: str, session_id: int, config_file: str, database_key: str, database_url: str, log_output: str = 'file', log_level: str = 'INFO'):
    """
    Runs the trading session with the provided configuration.
    """
    mode_enum = Mode[mode]
    strategy_cls = load_strategy_class(strategy_module, strategy_class)
    params = Parameters.from_file(config_file)

    config = Config(
        session_id=session_id,
        mode=mode_enum,
        params=params,
        database_key=database_key,
        database_url=database_url,
        logger_output=log_output,
        logger_level=getattr(logging, log_level)
    )

    config.set_strategy(strategy_cls)

    if mode_enum == Mode.LIVE:
        controller = LiveEventController(config)
    elif mode_enum == Mode.BACKTEST:
        controller = BacktestEventController(config)
    
    controller.run()

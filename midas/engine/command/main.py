# main.py
import logging
from .config import Config, Mode
from .parameters import Parameters
from midas.engine.risk import load_risk_class
from midas.engine.strategies import load_strategy_class
from .controller import LiveEventController, BacktestEventController

def run(mode: str, strategy_module: str, strategy_class: str, session_id: int, config_file: str, database_key: str, database_url: str, risk_module:str=None, risk_class: str=None, log_output: str='file', log_level: str='INFO', output_path: str=""):
    """
    Runs the trading session with the provided configuration.
    """
    # Configure user passed arguements
    mode_enum = Mode[mode]
    params = Parameters.from_file(config_file)
    strategy_cls = load_strategy_class(strategy_module, strategy_class)

    # Intialize config
    config = Config(
        session_id=session_id,
        mode=mode_enum,
        params=params,
        database_key=database_key,
        database_url=database_url,
        logger_output=log_output,
        logger_level=getattr(logging, log_level),
        output_path=output_path,
    )

    # Set Risk Model
    if risk_module and risk_class:
        risk_cls = load_risk_class(risk_module, risk_class)
        config.set_risk_model(risk_cls)
        
    # Set Strategy
    config.set_strategy(strategy_cls)

    # Initializer Event Controller
    if mode_enum == Mode.LIVE:
        controller = LiveEventController(config)
    elif mode_enum == Mode.BACKTEST:
        controller = BacktestEventController(config)
    
    # Run system
    controller.run()

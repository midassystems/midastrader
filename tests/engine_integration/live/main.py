# main.py
from .config import CointegrationzscoreConfig
from engine.command import EventController, Mode

def main():
    # Set the mode (LIVE or BACKTEST)
    mode = Mode.LIVE
    
    # Initialize the strategy configuration
    strategy_config = CointegrationzscoreConfig(mode=mode)

    # Initialize the event driver
    event_driver = EventController(strategy_config)
    event_driver.run()

if __name__ == "__main__":
    main()

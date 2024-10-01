import argparse
from midas.engine.engine import EngineBuilder


def run(config_path: str):
    """
    This function initializes the trading engine using the given config file.
    It creates all necessary components (logger, database, strategy, etc.)
    and starts the engine for either live trading or backtesting.

    :param config_path: Path to the configuration file (e.g., config.toml).
    """
    # Build the engine using the EngineBuilder
    engine = (
        EngineBuilder(config_path)
        .create_logger()  # Initialize logging
        .create_parameters()  # Load and parse the parameters
        .create_database_client()  # Set up the database client
        .create_symbols_map()  # Create the map for the trading symbols
        .create_core_components()  # Initialize order book, portfolio, etc.
        .create_gateways()  # Set up live or backtest gateways
        .create_observers()  # Set up the observer (for live trading)
        .build()  # Finalize the engine setup
    )

    # Initialize and start the engine
    engine.initialize()
    engine.start()


def main():
    """
    This is the main entry point for running the `midas` engine. It parses
    the command-line arguments and passes the config file path to the `run()` function.
    """
    # Parse the command-line argument (the config path)
    parser = argparse.ArgumentParser(
        description="Run the Midas trading engine"
    )
    parser.add_argument(
        "config", help="Path to the configuration file (e.g., config.toml)"
    )

    args = parser.parse_args()

    # Call the `run` function with the provided config file
    run(args.config)


if __name__ == "__main__":
    # The main entry point when this module is called with `python -m midas.engine.main`
    main()

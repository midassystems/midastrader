import argparse
from midastrader.config import Mode
from midastrader.engine import EngineBuilder


def run(config_path: str, mode: str):
    """
    Initializes and runs the Midas trading engine based on the provided configuration
    file and mode.

    This function builds all required components such as logging, database client,
    symbol maps, and gateways, then starts the engine for live trading or backtesting.

    Args:
        config_path (str): The path to the configuration file (e.g., "config.toml").
        mode (str): The mode to run the engine in. Must be either "BACKTEST" or "LIVE".

    Raises:
        KeyError: If an invalid mode is passed that is not defined in the `Mode` enum.

    Example:
        run("config.toml", "backtest")
    """
    mode = Mode[mode.upper()]

    # Build the engine using the EngineBuilder
    engine = (
        EngineBuilder(config_path, mode)
        .create_logger()
        .create_messagebus()
        .create_parameters()  # Load and parse the parameters
        .create_symbols_map()  # Create the map for the trading symbols
        .create_data_engine()  # Initialize logging
        .create_execution_engine()
        .create_core_engine()
        .build()  # Finalize the engine setup
    )

    # # Initialize and start the engine
    engine.initialize()
    engine.start()


def main():
    """
    Entry point for running the Midas trading engine.

    This function parses command-line arguments to determine the configuration file path
    and the mode in which to run the engine (live trading or backtesting). It then
    invokes the `run` function with these arguments.

    Command-line Arguments:
        config (str): Path to the configuration file (e.g., "config.toml").
        mode (str): The mode to run the engine, either "backtest" or "live".

    Example Usage:
        python -m midastrader.engine.main config.toml backtest

    Raises:
        argparse.ArgumentError: If required arguments are not provided.
    """
    # Parse the command-line argument (the config path)
    parser = argparse.ArgumentParser(
        description="Run the Midas trading engine"
    )
    parser.add_argument(
        "config",
        help="Path to the configuration file (e.g., config.toml)",
    )
    parser.add_argument(
        "mode",
        help="Engine mode (Backtest or Live)",
    )

    args = parser.parse_args()

    run(args.config, args.mode)


if __name__ == "__main__":
    # The main entry point when this module is called with `python -m midastrader.engine.main`
    main()

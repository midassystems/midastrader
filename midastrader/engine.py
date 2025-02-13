import threading
import signal

from midastrader.structs.symbol import SymbolMap
from midastrader.config import Parameters, Config, Mode
from midastrader.utils.logger import SystemLogger
from midastrader.core.adapters import OrderBook
from midastrader.core.adapters.base_strategy import load_strategy_class
from midastrader.data import DataEngine
from midastrader.execution import ExecutionEngine
from midastrader.message_bus import MessageBus
from midastrader.core import CoreEngine


class EngineBuilder:
    """
    A builder class to initialize and assemble the components of a trading system.

    This class builds various components needed for live or backtest trading environments,
    such as the logger, database client, symbol map, order book, gateways, observers,
    and other core trading components.

    Args:
        config_path (str): Path to the configuration file (TOML format).
        mode (Mode): The mode for the trading system, either `LIVE` or `BACKTEST`.

    Methods:
        create_logger(): Initializes the logging system.
        create_parameters(): Loads trading strategy parameters from the configuration file.
        create_database_client(): Sets up the database client for data access.
        create_symbols_map(): Builds a symbol map for all trading instruments.
        create_core_components(): Creates the order book, portfolio server, and performance manager.
        create_gateways(): Initializes data and broker clients based on the selected mode.
        create_observers(): Connects components through observers for live or backtest events.
        build(): Finalizes and returns the fully constructed trading system.
    """

    def __init__(self, config_path: str, mode: Mode):
        """
        Initialize the EngineBuilder with the configuration path and mode.

        Args:
            config_path (str): Path to the configuration file.
            mode (Mode): Mode of operation, either `Mode.LIVE` or `Mode.BACKTEST`.
        """
        self.mode = mode
        self.config = self.load_config(config_path)

        self.logger = self.create_logger()
        self.bus = self.create_messagebus()
        self.params = self.create_parameters()
        self.symbols_map = self.create_symbols_map()
        self.data_engine = self.create_data_engine()
        self.execution_engine = self.create_execution_engine()
        self.core_engine = self.create_core_engine()

    def load_config(self, config_path: str) -> Config:
        """
        Load the trading system configuration from a TOML file.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            Config: An instance of the Config class with all loaded parameters.
        """
        return Config.from_toml(config_path)

    def create_logger(self) -> SystemLogger:
        """
        Create the system logger for logging output.

        The logger outputs messages to the configured file or terminal
        depending on the settings in the configuration.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        return SystemLogger(
            self.config.strategy_parameters["strategy_name"],
            self.config.log_output,
            self.config.output_path,
            self.config.log_level,
        )

    def create_messagebus(self) -> MessageBus:
        return MessageBus()

    def create_orderbook(self) -> OrderBook:
        """
        Create the system logger for logging output.

        The logger outputs messages to the configured file or terminal
        depending on the settings in the configuration.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        return OrderBook()

    def create_symbols_map(self) -> SymbolMap:
        """
        Create the symbol map for all trading instruments.

            Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        symbols_map = SymbolMap()

        for symbol in self.params.symbols:
            symbols_map.add_symbol(symbol=symbol)
        return symbols_map

    def create_parameters(self) -> Parameters:
        """
        Create and load trading parameters from the configuration.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        return Parameters.from_dict(self.config.strategy_parameters)

    def create_data_engine(self) -> DataEngine:
        data_engine = DataEngine(
            self.symbols_map,
            self.bus,
            self.mode,
            self.params,
        )
        data_engine.construct_adaptors(self.config.vendors)

        return data_engine

    def create_execution_engine(self) -> ExecutionEngine:
        execution_engine = ExecutionEngine(
            self.symbols_map,
            self.bus,
            self.mode,
            self.params,
        )
        execution_engine.initialize_adaptors(self.config.executors)

        return execution_engine

    def create_core_engine(self) -> CoreEngine:
        core_engine = CoreEngine(
            self.symbols_map,
            self.bus,
            self.mode,
            self.params,
            self.config.output_path,
        )
        core_engine.initialize()

        return core_engine

    def build(self) -> "Engine":
        """
        Finalize and return the fully constructed trading system engine.

        Returns:
            Engine: The assembled trading engine instance ready for execution.
        """
        return Engine(
            mode=self.mode,
            config=self.config,
            bus=self.bus,
            symbols_map=self.symbols_map,
            params=self.params,
            core_engine=self.core_engine,
            data_engine=self.data_engine,
            execution_engine=self.execution_engine,
        )


class Engine:
    """
    A class representing the core trading engine for both live and backtest modes.

    This class manages the initialization, setup, and execution of the trading system. It handles
    data feeds, order management, risk models, and strategies while maintaining an event-driven
    architecture.

    Args:
        mode (Mode): Mode of the trading system, either `LIVE` or `BACKTEST`.
        config (Config): Configuration object containing all system parameters.
        event_queue (queue.Queue): Queue for managing events.
        symbols_map (SymbolMap): Map of trading symbols.
        params (Parameters): Strategy and trading parameters.
        order_book (OrderBook): Order book for managing market data.
        portfolio_server (PortfolioServer): Server managing portfolio positions and accounts.
        performance_manager (PerformanceManager): Manager tracking trading system performance.
        order_manager (OrderExecutionManager): Manager for order execution.
        observer (Optional[DatabaseUpdater]): Observer for database updates.
        live_data_client (Optional[LiveDataClient]): Client for live market data feeds.
        hist_data_client (BacktestDataClient): Client for historical backtest data.
        broker_client (Union[LiveBrokerClient, BacktestBrokerClient]): Client for broker operations.

    Methods:
        initialize(): Initialize the system components.
        setup_live_environment(): Configure the trading environment for live mode.
        setup_backtest_environment(): Configure the trading environment for backtesting.
        _load_live_data(): Load and subscribe to live market data feeds.
        _load_historical_data(): Load historical data for backtesting.
        set_risk_model(): Initialize and attach the risk model.
        set_strategy(): Load and initialize the trading strategy.
        start(): Start the main event loop based on the mode.
        stop(): Gracefully shut down the trading engine.
        _signal_handler(signum, frame): Handle system signals for shutdown.
    """

    def __init__(
        self,
        mode: Mode,
        config: Config,
        bus: MessageBus,
        symbols_map: SymbolMap,
        params: Parameters,
        core_engine: CoreEngine,
        data_engine: DataEngine,
        execution_engine: ExecutionEngine,
    ):
        """
        Initialize the trading engine with all required components.

        Args:
            mode (Mode): The trading system mode (`LIVE` or `BACKTEST`).
            config (Config): Configuration object for the system.
            event_queue (queue.Queue): Event queue for event-driven operations.
            symbols_map (SymbolMap): Map of trading symbols.
            params (Parameters): Strategy and trading parameters.
            order_book (OrderBook): Order book for managing market data.
            portfolio_server (PortfolioServer): Portfolio manager for positions and accounts.
            performance_manager (PerformanceManager): Manager to monitor performance.
            order_manager (OrderExecutionManager): Handles order execution.
            observer (Optional[DatabaseUpdater]): Observer for database updates.
            live_data_client (Optional[LiveDataClient]): Client for live data feeds.
            hist_data_client (BacktestDataClient): Client for backtest historical data.
            broker_client (Union[LiveBrokerClient, BacktestBrokerClient]): Broker client for order routing.
        """
        self.mode = mode
        self.config = config
        self.bus = bus
        self.symbols_map = symbols_map
        self.logger = SystemLogger.get_logger()
        self.parameters = params
        self.core_engine = core_engine
        self.data_engine = data_engine
        self.execution_engine = execution_engine
        self.threads = {}

    def initialize(self):
        """
        Initialize the trading system by setting up all required components.

        Depending on the mode (live or backtest), this method configures the system's data feeds,
        risk models, and trading strategies.

        Raises:
            RuntimeError: If the system fails to load required components.
        """
        # Risk Model
        if self.config.risk_class:
            self.core_engine.set_risk_model()

        # Strategy
        strategy_class = load_strategy_class(
            self.config.strategy_module,
            self.config.strategy_class,
        )

        strategy = strategy_class(self.symbols_map, self.bus)
        self.core_engine.set_strategy(strategy)

    def start(self):
        """
        Start the main event loop of the trading system.
        """
        self.logger.info(f"<< Starting in {self.mode.value} mode. >>\n")

        # Start engines
        core_thread = threading.Thread(target=self.core_engine.start)
        core_thread.start()
        self.core_engine.running.wait()

        exeution_thread = threading.Thread(target=self.execution_engine.start)
        exeution_thread.start()
        self.execution_engine.running.wait()

        data_thread = threading.Thread(target=self.data_engine.start)
        data_thread.start()
        self.data_engine.running.wait()

        if self.mode == Mode.BACKTEST:
            self._backtest_loop()
        else:
            self._live_loop()

        for thread in self.threads:
            thread.join()  # Wait for each thread to finish

        self.logger.info(f"\n<< Ending {self.mode.value} >>")

    def _backtest_loop(self):
        """
        Event loop for backtesting.
        """
        # Wait for DataEngine to complete
        self.data_engine.wait_until_complete()
        self.data_engine.stop()

        # Shut down engines in order
        self.core_engine.stop()

        self.execution_engine.stop()
        self.core_engine.save()
        self.core_engine.wait_until_complete()

        self.logger.info("Backtest completed ...")

    def _live_loop(self):
        """Event loop for live trading."""
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)

        while self.running:
            continue

        # Perform cleanup here
        self.data_engine.stop()

        # Finalize and save to database
        self.execution_engine.stop()

        self.core_engine.save()

        self.logger.info("Live completed ...")

    def _signal_handler(self, signum, frame):
        """
        Handle system signals (e.g., SIGINT) to stop the event loop.

        Args:
            signum (int): Signal number.
            frame: Current stack frame.
        """
        self.logger.info("Signal received, preparing to shut down.")
        self.running = False  # Stop the event loop

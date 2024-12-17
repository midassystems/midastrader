import time
import queue
import signal
from typing import Union, Optional
from midas.symbol import SymbolMap
from midasClient.client import DatabaseClient
from midas.engine.components.order_book import OrderBook
from midas.engine.components.observer.database_updater import DatabaseUpdater
from midas.utils.logger import SystemLogger
from midas.engine.components.portfolio_server import PortfolioServer
from midas.engine.components.order_manager import OrderExecutionManager
from midas.engine.components.risk.risk_handler import RiskHandler
from midas.engine.components.performance.base import PerformanceManager
from midas.engine.config import Parameters
from midas.engine.components.base_strategy import load_strategy_class
from midas.engine.config import Config, Mode
from midas.engine.components.observer.base import EventType
from midas.engine.components.gateways.backtest import (
    DataClient as BacktestDataClient,
    BrokerClient as BacktestBrokerClient,
    DummyBroker,
)
from midas.engine.components.gateways.live import (
    DataClient as LiveDataClient,
    BrokerClient as LiveBrokerClient,
    ContractManager,
)


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
        self.config = self._load_config(config_path)
        self.event_queue = queue.Queue()
        self.params = None
        self.database_client = None
        self.symbols_map = None
        self.order_book = None
        self.portfolio_server = None
        self.order_manager = None
        self.observer = None
        self.performance_manager = None
        self.hist_data_client = None
        self.broker_client = None
        self.live_data_client = None
        self.dummy_broker = None
        self.eod_event_flag = None

    def _load_config(self, config_path: str) -> Config:
        """
        Load the trading system configuration from a TOML file.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            Config: An instance of the Config class with all loaded parameters.
        """
        return Config.from_toml(config_path)

    def create_logger(self):
        """
        Create the system logger for logging output.

        The logger outputs messages to the configured file or terminal
        depending on the settings in the configuration.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        SystemLogger(
            self.config.strategy_parameters["strategy_name"],
            self.config.log_output,
            self.config.output_path,
            self.config.log_level,
        )
        return self

    def create_parameters(self):
        """
        Create and load trading parameters from the configuration.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        self.params = Parameters.from_dict(self.config.strategy_parameters)
        return self

    def create_database_client(self):
        """
        Initialize the database client for data access.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        self.database_client = DatabaseClient()
        return self

    def create_symbols_map(self):
        """
        Create the symbol map for all trading instruments.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        self.symbols_map = SymbolMap()
        # symbols = self.params.symbols

        for symbol in self.params.symbols:
            self.symbols_map.add_symbol(symbol=symbol)
        return self

    def create_core_components(self):
        """
        Create the core components of the trading system:
        - OrderBook: Manages market data and order book updates.
        - PortfolioServer: Tracks positions and account updates.
        - OrderExecutionManager: Handles order execution.
        - PerformanceManager: Tracks system performance.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        self.order_book = OrderBook(self.symbols_map)
        self.portfolio_server = PortfolioServer(self.symbols_map)
        self.order_manager = OrderExecutionManager(
            self.symbols_map,
            self.order_book,
            self.portfolio_server,
        )
        self.performance_manager = PerformanceManager(
            self.database_client,
            self.params,
            self.symbols_map,
        )
        return self

    def create_gateways(self):
        """
        Create data and broker clients depending on the mode (LIVE or BACKTEST).

        For live mode, the system uses live data and broker clients.
        For backtesting, it initializes historical data clients and dummy brokers.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        if self.mode == Mode.LIVE:
            self.hist_data_client = BacktestDataClient(
                self.database_client,
                self.symbols_map,
            )
            self.live_data_client = LiveDataClient(
                self.config,
                self.symbols_map,
            )
            self.broker_client = LiveBrokerClient(
                self.config,
                self.symbols_map,
            )

        else:
            self.hist_data_client = BacktestDataClient(
                self.database_client,
                self.symbols_map,
            )
            self.dummy_broker = DummyBroker(
                self.symbols_map,
                self.order_book,
                self.config.strategy_parameters.get("capital", 0),
            )
            self.broker_client = BacktestBrokerClient(
                self.dummy_broker,
                self.symbols_map,
            )
        return self

    def create_observers(self):
        """
        Attach observers to system components to handle event updates.

        - For backtesting, observers include dummy brokers, order books, and clients.
        - For live mode, observers include real-time data and broker clients.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """
        if self.mode == Mode.BACKTEST:
            self.hist_data_client.attach(
                self.dummy_broker, EventType.EOD_EVENT
            )
            self.hist_data_client.attach(
                self.order_book, EventType.MARKET_DATA
            )
            self.order_book.attach(self.broker_client, EventType.ORDER_BOOK)
            self.dummy_broker.attach(
                self.broker_client, EventType.TRADE_EXECUTED
            )
            self.dummy_broker.attach(self.broker_client, EventType.EOD_EVENT)
            self.broker_client.attach(
                self.portfolio_server, EventType.POSITION_UPDATE
            )
            self.broker_client.attach(
                self.portfolio_server, EventType.ACCOUNT_UPDATE
            )
            self.broker_client.attach(
                self.performance_manager, EventType.TRADE_UPDATE
            )
            self.broker_client.attach(
                self.performance_manager, EventType.EQUITY_VALUE_UPDATE
            )
            self.order_manager.attach(
                self.broker_client, EventType.ORDER_CREATED
            )

        if self.mode == Mode.LIVE:
            self.live_data_client.app.attach(
                self.order_book, EventType.MARKET_DATA
            )
            self.broker_client.app.attach(
                self.portfolio_server, EventType.POSITION_UPDATE
            )
            self.broker_client.app.attach(
                self.portfolio_server, EventType.ACCOUNT_UPDATE
            )
            self.broker_client.app.attach(
                self.performance_manager, EventType.TRADE_UPDATE
            )
            self.broker_client.app.attach(
                self.performance_manager, EventType.EQUITY_VALUE_UPDATE
            )
            self.order_manager.attach(
                self.broker_client, EventType.ORDER_CREATED
            )
            self.broker_client.app.attach(
                self.portfolio_server, EventType.ORDER_UPDATE
            )

        return self

    def build(self):
        """
        Finalize and return the fully constructed trading system engine.

        Returns:
            Engine: The assembled trading engine instance ready for execution.
        """
        return Engine(
            mode=self.mode,
            config=self.config,
            event_queue=self.event_queue,
            symbols_map=self.symbols_map,
            params=self.params,
            order_book=self.order_book,
            portfolio_server=self.portfolio_server,
            performance_manager=self.performance_manager,
            order_manager=self.order_manager,
            observer=self.observer,
            live_data_client=(
                self.live_data_client if self.live_data_client else None
            ),
            hist_data_client=self.hist_data_client,
            broker_client=self.broker_client,
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
        event_queue: queue.Queue,
        symbols_map: SymbolMap,
        params: Parameters,
        order_book: OrderBook,
        portfolio_server: PortfolioServer,
        performance_manager: PerformanceManager,
        order_manager: OrderExecutionManager,
        observer: Optional[DatabaseUpdater],
        live_data_client: Optional[LiveDataClient],
        hist_data_client: BacktestDataClient,
        broker_client: Union[LiveBrokerClient, BacktestBrokerClient],
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
        self.event_queue = event_queue
        self.symbols_map = symbols_map
        self.logger = SystemLogger.get_logger()
        self.parameters = params
        self.order_book = order_book
        self.portfolio_server = portfolio_server
        self.performance_manager = performance_manager
        self.order_manager = order_manager
        self.observer = observer
        self.live_data_client = live_data_client
        self.hist_data_client = hist_data_client
        self.broker_client = broker_client
        self.strategy = None
        self.contract_manager = None
        self.risk_model = None
        self.train_data = None

    def initialize(self):
        """
        Initialize the trading system by setting up all required components.

        Depending on the mode (live or backtest), this method configures the system's data feeds,
        risk models, and trading strategies.

        Raises:
            RuntimeError: If the system fails to load required components.
        """
        self.logger.info(f"Initializing system with mode: {self.mode.value}")

        if self.mode == Mode.LIVE:
            self.logger.info("Setting up live environment...")
            self.setup_live_environment()
        else:
            self.logger.info("Setting up backtest environment...")
            self.setup_backtest_environment()

        # Risk Model
        self.set_risk_model()

        # Strategy
        self.set_strategy()

        self.logger.info("Trading system initialized successfully.")

    def setup_live_environment(self):
        """
        Configure the live trading environment.

        Establishes connections to live data feeds, brokers, and validates trading contracts.

        Raises:
            RuntimeError: If contract validation fails or live data cannot be loaded.
        """
        # Set up connections
        self.broker_client.connect()

        # Validate Contracts
        self.contract_handler = ContractManager(self.broker_client)
        for symbol in self.symbols_map.symbols:
            if not self.contract_handler.validate_contract(symbol.contract):
                raise RuntimeError(f"{symbol.broker_ticker} invalid contract.")

        # Laod Hist Data
        self._load_historical_data()

        # Load Live Data
        self.live_data_client.connect()
        self._load_live_data()

    def setup_backtest_environment(self):
        """
        Configure the backtest environment.

        Loads historical data needed for simulation and backtesting.
        Raises:
            RuntimeError: If backtest data cannot be loaded.
        """
        self._load_historical_data()

    def _load_live_data(self):
        """
        Subscribe to live data feeds for the trading symbols.

        Raises:
            ValueError: If live data fails to load for any symbol.
        """
        try:
            for symbol in self.symbols_map.symbols:
                self.live_data_client.get_data(
                    data_type=self.parameters.data_type,
                    contract=symbol.contract,
                )
        except ValueError:
            raise ValueError(f"Error loading live data for {symbol.ticker}.")

    def _load_historical_data(self):
        """
        Load historical data for backtesting.

        Raises:
            RuntimeError: If the backtest data fails to load.
        """
        response = self.hist_data_client.load_backtest_data(
            self.symbols_map.midas_tickers,
            self.parameters.start,
            self.parameters.end,
            self.parameters.schema,
            self.config.data_file,
        )

        if response:
            self.logger.info("Backtest data loaded.")
        else:
            raise RuntimeError("Backtest data did not load.")

    def set_risk_model(self):
        """
        Initialize and set the risk model for the trading system.

        Attaches the risk model to the database observer to track risk updates.
        """
        if self.config.risk_class:
            self.risk_model = RiskHandler(self.config.risk_class)

            # Attach the DatabaseUpdater as an observer to RiskModel
            self.risk_model.attach(
                self.observer,
                EventType.RISK_MODEL_UPDATE,
            )
            self.logger.info("Risk model set successfully.")

    def set_strategy(self):
        """
        Load and initialize the trading strategy.

        Attaches the strategy to key components such as the order book, order manager, and performance manager.
        """
        strategy_class = load_strategy_class(
            self.config.strategy_module,
            self.config.strategy_class,
        )

        self.strategy = strategy_class(
            symbols_map=self.symbols_map,
            portfolio_server=self.portfolio_server,
            order_book=self.order_book,
            hist_data_client=self.hist_data_client,
        )
        self.performance_manager.set_strategy(self.strategy)
        self.order_book.attach(self.strategy, EventType.ORDER_BOOK)
        self.strategy.attach(self.order_manager, EventType.SIGNAL)
        self.strategy.attach(self.performance_manager, EventType.SIGNAL)
        self.strategy.primer()
        self.logger.info("Strategy set successfully.")

    def start(self):
        """
        Start the main event loop of the trading system.

        Depending on the mode, it either runs live trading or backtesting.
        """
        self.logger.info(f"* Starting event loop in {self.mode.value} mode. *")

        if self.mode == Mode.LIVE:
            self._run_live_event_loop()
        else:
            self._run_backtest_event_loop()

        self.logger.info("Event loop ended.")

    def _run_live_event_loop(self):
        """Event loop for live trading."""
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)

        while self.running:
            continue

        # Perform cleanup here
        self.database_updater.delete_session()

        # Finalize and save to database
        self.broker_client.request_account_summary()
        time.sleep(5)  # time for final account summary request-maybe shorten
        self.performance_manager.save()

    def _run_backtest_event_loop(self):
        """Event loop for backtesting."""
        # Load Initial account data
        self.broker_client.update_account()

        while self.hist_data_client.data_stream():
            continue

        # Perform EOD operations for the last trading day
        self.broker_client.liquidate_positions()

        # Finalize and save to database
        self.performance_manager.save(self.mode, self.config.output_path)

    def stop(self):
        """
        Gracefully shut down the trading engine.

        Disconnects live data feeds and performs cleanup operations.
        """
        self.logger.info("Shutting down the engine.")
        if self.mode == Mode.LIVE:
            self.live_data_client.disconnect()
        self.logger.info("Engine shutdown complete.")

    def _signal_handler(self, signum, frame):
        """
        Handle system signals (e.g., SIGINT) to stop the event loop.

        Args:
            signum (int): Signal number.
            frame: Current stack frame.
        """
        self.logger.info("Signal received, preparing to shut down.")
        self.running = False  # Stop the event loop

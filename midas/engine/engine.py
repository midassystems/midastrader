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
    def __init__(self, config_path: str, mode: Mode):
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
        """Load the configuration from the TOML file."""
        return Config.from_toml(config_path)

    def create_logger(self):
        """Step 1: Create logger"""
        SystemLogger(
            self.config.strategy_parameters["strategy_name"],
            self.config.log_output,
            self.config.output_path,
            self.config.log_level,
        )
        return self

    def create_parameters(self):
        self.params = Parameters.from_dict(self.config.strategy_parameters)
        return self

    def create_database_client(self):
        """Step 2: Create database client"""
        self.database_client = DatabaseClient()
        return self

    def create_symbols_map(self):
        """Step 3: Create symbols map from strategy parameters"""
        self.symbols_map = SymbolMap()
        # symbols = self.params.symbols

        for symbol in self.params.symbols:
            self.symbols_map.add_symbol(symbol=symbol)
        return self

    def create_core_components(self):
        """Step 4: Create order book, portfolio server, and order manager"""
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
        """Step 5: Create data and broker clients (for live and backtest)"""
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
        """Step 5: Create observer (for live mode only)"""
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
        """Finalize and return the built trading system"""
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
        self.live_data_client = live_data_client  # live data client
        self.hist_data_client = hist_data_client  # historical data client
        self.broker_client = broker_client
        self.strategy = None
        self.contract_manager = None
        self.risk_model = None
        self.train_data = None

    def initialize(self):
        """
        Initialize the trading system by setting up all the components.
        This is where you could trigger any final setup or pre-run checks.
        """
        self.logger.info(
            f"Initializing trading system with mode: {self.mode.value}"
        )

        # Initialize components based on the mode (live or backtest)
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
        Set up the live trading environment, including data feeds and broker client.
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
        Set up the backtest environment, including loading historical data.
        """
        self._load_historical_data()
        # Load Train Data

        # Load Backtest Data
        # self._load_backtest_data()

    def _load_live_data(self):
        """
        Loads and subscribes to live data feeds for the symbols in the strategy.
        """
        try:
            for symbol in self.symbols_map.symbols:
                self.live_data_client.get_data(
                    data_type=self.parameters.data_type,
                    contract=symbol.contract,
                )
        except ValueError:
            raise ValueError(
                f"Error loading live data for symbol {symbol.ticker}."
            )

    def _load_historical_data(self):
        """
        Loads backtest data for the period specified in the parameters.
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

    # def _load_train_data(self):
    #     """
    #     Loads histroical training data for the period specified in the parameters.
    #     """
    #     self.train_data = self.hist_data_client.get_data(
    #         self.symbols_map.midas_tickers,
    #         self.parameters.train_start,
    #         self.parameters.train_end,
    #         self.parameters.schema,
    #         self.config.train_data_file,
    #     )
    #     self.logger.info("Training data loaded.")
    #
    # def _load_backtest_data(self):
    #     """
    #     Loads backtest data for the period specified in the parameters.
    #     """
    #
    #     response = self.hist_data_client.load_backtest_data(
    #         self.symbols_map.midas_tickers,
    #         self.parameters.test_start,
    #         self.parameters.test_end,
    #         self.parameters.schema,
    #         self.config.test_data_file,
    #     )
    #
    #     if response:
    #         self.logger.info("Backtest data loaded.")
    #     else:
    #         raise RuntimeError("Backtest data did not load.")

    def set_risk_model(self):
        """
        Set a risk model for the trading system.
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
        """Step 7: Set up strategy (both live and backtest)"""
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

        # self.strategy.prepare(self.train_data)
        self.strategy.primer()
        self.logger.info("Strategy set successfully.")

    def start(self):
        """Run the engine's event loop for live trading or backtesting."""
        self.logger.info(
            f"*** Starting event loop in {self.mode.value} mode. ***"
        )

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
        """Gracefully shut down the engine."""
        self.logger.info("Shutting down the engine.")
        if self.mode == Mode.LIVE:
            self.live_data_client.disconnect()
        self.logger.info("Engine shutdown complete.")

    def _signal_handler(self, signum, frame):
        """Handles signals like SIGINT to gracefully shut down the event loop."""
        self.logger.info("Signal received, preparing to shut down.")
        self.running = False  # Stop the event loop

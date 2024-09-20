import time
import queue
import threading
import signal
from typing import Union, Optional
from midas.symbol import SymbolMap
from midasClient.client import DatabaseClient
from midas.engine.components.observer import EventType
from midas.engine.components.order_book import OrderBook
from midas.engine.components.observer.database_updater import DatabaseUpdater
from midas.utils.logger import SystemLogger
from midas.engine.components.portfolio_server import PortfolioServer
from midas.engine.components.order_manager import OrderManager
from midas.engine.components.risk.risk_handler import RiskHandler
from midas.engine.components.performance.base import BasePerformanceManager
from midas.engine.components.performance.live import LivePerformanceManager
from midas.engine.config import Parameters
from midas.engine.components.performance.backtest import (
    BacktestPerformanceManager,
)
from midas.engine.components.base_strategy import load_strategy_class
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
from midas.engine.config import Config, Mode
from midas.engine.events import (
    MarketEvent,
    OrderEvent,
    SignalEvent,
    ExecutionEvent,
    EODEvent,
)


class EngineBuilder:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.event_queue = queue.Queue()
        self.logger = None
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
        self.logger = SystemLogger(
            self.config.strategy_parameters["strategy_name"],
            self.config.log_output,
            self.config.output_path,
            self.config.log_level,
        ).logger
        return self

    def create_parameters(self):
        self.params = Parameters.from_dict(self.config.strategy_parameters)
        return self

    def create_database_client(self):
        """Step 2: Create database client"""
        self.database_client = DatabaseClient(self.config.database_url)
        return self

    def create_symbols_map(self):
        """Step 3: Create symbols map from strategy parameters"""
        self.symbols_map = SymbolMap()
        symbols = self.params.symbols

        for symbol in symbols:
            self.symbols_map.add_symbol(symbol.ticker, symbol)
        # self.symbols_map = symbol_map
        return self

    def create_core_components(self):
        """Step 4: Create order book, portfolio server, and order manager"""
        self.order_book = OrderBook(self.event_queue)
        self.portfolio_server = PortfolioServer(
            self.symbols_map,
            self.logger,
            self.database_client,
        )
        self.order_manager = OrderManager(
            self.symbols_map,
            self.event_queue,
            self.order_book,
            self.portfolio_server,
            self.logger,
        )
        return self

    def create_observer(self):
        """Step 5: Create observer (for live mode only)"""
        if self.config.mode == Mode.LIVE:
            self.observer = DatabaseUpdater(
                self.database_client,
                self.config.session_id,
            )
            self.order_book.attach(self.observer, EventType.MARKET_EVENT)
            self.portfolio_server.attach(
                self.observer,
                EventType.POSITION_UPDATE,
            )
            self.config.portfolio_server.attach(
                self.observer,
                EventType.ORDER_UPDATE,
            )
            self.config.portfolio_server.attach(
                self.observer,
                EventType.ACCOUNT_DETAIL_UPDATE,
            )
        return self

    def create_performance_manager(self):
        """Step 6: Create performance manager based on mode"""
        if self.config.mode == Mode.LIVE:
            self.performance_manager = LivePerformanceManager(
                self.database_client,
                self.logger,
                self.config.strategy_parameters,
            )
        else:
            self.performance_manager = BacktestPerformanceManager(
                self.database_client,
                self.logger,
                self.config.strategy_parameters,
                None,
            )
        return self

    def create_gateways(self):
        """Step 7: Create data and broker clients (for live and backtest)"""
        if self.config.mode == Mode.LIVE:
            self.hist_data_client = BacktestDataClient(
                self.config.event_queue,
                self.config.database,
                self.config.order_book,
                None,
            )
            self.live_data_client = LiveDataClient(
                self.event_queue, self.order_book, self.logger
            )
            self.broker_client = LiveBrokerClient(
                self.event_queue,
                self.logger,
                self.portfolio_server,
                self.performance_manager,
            )
        else:
            self.eod_event_flag = threading.Event()
            self.hist_data_client = BacktestDataClient(
                self.event_queue,
                self.database_client,
                self.order_book,
                self.eod_event_flag,
            )
            self.dummy_broker = DummyBroker(
                self.symbols_map,
                self.event_queue,
                self.order_book,
                self.config.strategy_parameters.get("capital", 0),
                self.logger,
            )
            self.broker_client = BacktestBrokerClient(
                self.event_queue,
                self.logger,
                self.portfolio_server,
                self.performance_manager,
                self.dummy_broker,
                self.eod_event_flag,
            )
        return self

    def build(self):
        """Finalize and return the built trading system"""
        return Engine(
            config=self.config,
            event_queue=self.event_queue,
            symbols_map=self.symbols_map,
            logger=self.logger,
            params=self.params,
            order_book=self.order_book,
            portfolio_server=self.portfolio_server,
            performance_manager=self.performance_manager,
            order_manager=self.order_manager,
            observer=self.observer,
            data_client=(
                self.live_data_client
                if self.live_data_client
                else self.hist_data_client
            ),
            hist_data_client=self.hist_data_client,
            broker_client=self.broker_client,
        )


class Engine:
    def __init__(
        self,
        config: Config,
        event_queue: queue.Queue,
        symbols_map: SymbolMap,
        logger: SystemLogger,
        params: Parameters,
        order_book: OrderBook,
        portfolio_server: PortfolioServer,
        performance_manager: BasePerformanceManager,
        order_manager: OrderManager,
        observer: Optional[DatabaseUpdater],
        data_client: Union[LiveDataClient, BacktestDataClient],
        hist_data_client: Optional[BacktestDataClient],
        broker_client: Union[LiveBrokerClient, BacktestBrokerClient],
    ):
        self.config = config
        self.event_queue = event_queue
        self.symbols_map = symbols_map
        self.logger = logger
        self.parameters = params
        self.order_book = order_book
        self.portfolio_server = portfolio_server
        self.performance_manager = performance_manager
        self.order_manager = order_manager
        self.observer = observer
        self.data_client = data_client  # live data client
        self.hist_data_client = hist_data_client  # historical data client
        self.broker_client = broker_client
        self.strategy = None
        self.contract_manager = None
        self.risk_model = None
        self.hist_data = None

    def initialize(self):
        """
        Initialize the trading system by setting up all the components.
        This is where you could trigger any final setup or pre-run checks.
        """
        self.logger.info(
            f"Initializing trading system with mode: {self.config.mode.value}"
        )

        # Initialize components based on the mode (live or backtest)
        if self.config.mode == Mode.LIVE:
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
        self.contract_handler = ContractManager(self.data_client, self.logger)
        for ticker, symbol in self.symbols_map.items():
            if not self.contract_handler.validate_contract(symbol.contract):
                raise RuntimeError(f"{ticker} invalid contract.")

        # Laod Hist Data
        self._load_hist_data()

        # Load Live Data
        self.data_client.connect()
        self._load_live_data()

    def setup_backtest_environment(self):
        """
        Set up the backtest environment, including loading historical data.
        """
        # Load Hist Data
        self._load_hist_data()

    def _load_live_data(self):
        """
        Loads and subscribes to live data feeds for the symbols in the strategy.
        """
        try:
            for _, symbol in self.symbols_map.items():
                self.data_client.get_data(
                    data_type=self.params.data_type,
                    contract=symbol.contract,
                )
        except ValueError:
            raise ValueError(
                f"Error loading live data for symbol {symbol.ticker}."
            )

    def _load_hist_data(self):
        """
        Loads historical data for the period specified in the parameters.
        """
        tickers = self.symbols_map.tickers
        response = self.hist_data_client.get_data(
            tickers,
            self.parameters.test_start,
            self.parameters.test_end,
            self.parameters.schema,
            self.config.data_file,
        )

        if response:
            self.logger.info("Backtest data loaded.")
            if self.config.mode == Mode.LIVE:
                self.hist_data = self.hist_data_client.data.decode_to_df()

                # # Extract contract details for mapping
                contracts_map = {
                    symbol.data_ticker: symbol.ticker
                    for symbol in self.symbols_map.symbols
                }
                self.hist_data["symbol"] = self.hist_data["symbol"].map(
                    contracts_map
                )
        else:
            raise RuntimeError("Backtest data did not load.")

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

        # strategy_class = self.config.strategy_class
        self.strategy = strategy_class(
            symbols_map=self.symbols_map,
            # historical_data=self.config.historical_data,
            portfolio_server=self.portfolio_server,
            logger=self.logger,
            order_book=self.order_book,
            event_queue=self.event_queue,
        )
        self.strategy.prepare(self.hist_data)
        self.logger.info("Strategy set successfully.")

    def start(self):
        """Run the engine's event loop for live trading or backtesting."""
        self.logger.info(
            f"*** Starting event loop in {self.config.mode.value} mode. ***"
        )

        if self.config.mode == Mode.LIVE:
            self._run_live_event_loop()
        else:
            self._run_backtest_event_loop()

        self.logger.info("Event loop ended.")

    def _run_live_event_loop(self):
        """Event loop for live trading."""
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)

        while self.running:
            while not self.event_queue.empty():
                event = self.event_queue.get()
                self.logger.info(event)
                self._handle_event(event)

        # Perform cleanup here
        self.database_updater.delete_session()

        # Finalize and save to database
        self.broker_client.request_account_summary()
        time.sleep(5)  # time for final account summary request-maybe shorten
        self.performance_manager.save()

    def _run_backtest_event_loop(self):
        """Event loop for backtesting."""
        while self.hist_data_client.data_stream():
            while not self.event_queue.empty():
                event = self.event_queue.get()
                self.logger.info(f"Processing event: {event}")
                self._handle_event(event)

        # Perform EOD operations for the last trading day
        self.broker_client.eod_update()
        self.broker_client.liquidate_positions()

        # Finalize and save to database
        self.performance_manager.save(self.output_path)

    def _handle_event(self, event):
        """Handles different event types (market data, signal, order, etc.)."""
        if isinstance(event, MarketEvent):
            if self.config.mode == Mode.BACKTEST:
                self.broker_client.update_equity_value()  # Updates equity value for backtests
            self.strategy.handle_market_data()

        elif isinstance(event, SignalEvent):
            self.performance_manager.update_signals(event)
            self.order_manager.on_signal(event)
            # self.s trategy.handle_signal(event)

        elif isinstance(event, OrderEvent):
            self.broker_client.on_order(event)

        elif isinstance(event, ExecutionEvent):
            self.broker_client.on_execution(event)

        elif isinstance(event, EODEvent):
            self.broker_client.eod_update()

    def _signal_handler(self, signum, frame):
        """Handles signals like SIGINT to gracefully shut down the event loop."""
        self.logger.info("Signal received, preparing to shut down.")
        self.running = False  # Stop the event loop

    def stop(self):
        """Gracefully shut down the engine."""
        self.logger.info("Shutting down the engine.")
        if self.config.mode == Mode.LIVE:
            self.data_client.disconnect()
        self.logger.info("Engine shutdown complete.")

    # def start(self):
    #     """
    #     Start the trading session, either live or backtest, by triggering the event controller.
    #     """
    #     controller = create_event_controller(self.config)
    #     controller.run()

    # def stop(self):
    #     """
    #     Gracefully shut down the trading system.
    #     """
    #     self.logger.info("Shutting down the trading system...")
    #     # You can add shutdown logic here like saving performance metrics or closing connections
    #     if self.config.mode == Mode.LIVE:
    #         self.data_client.disconnect()
    #     self.logger.info("Trading system shutdown complete.")

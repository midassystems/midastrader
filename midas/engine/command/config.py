import queue
import logging
import threading
from enum import Enum
import pandas as pd
from typing import Union, Dict
from decouple import config
from abc import ABC, abstractmethod

from midas.shared.symbol import Symbol
from midas.client import DatabaseClient
from midas.engine.observer import EventType
from midas.engine.order_book import OrderBook
from midas.engine.strategies import BaseStrategy
from midas.engine.risk_model import BaseRiskModel
from midas.engine.data_sync import DatabaseUpdater
from midas.shared.utils.logger import SystemLogger
from midas.engine.portfolio import PortfolioServer
from midas.engine.order_manager import OrderManager
from midas.engine.gateways.live import ContractManager
from midas.engine.command.parameters import Parameters
from midas.engine.gateways.live import DataClient as LiveDataClient
from midas.engine.performance.base_manager import BasePerformanceManager
from midas.engine.gateways.backtest.data_client import DataClient as HistoricalDataClient

class Mode(Enum):
    LIVE = "LIVE"
    BACKTEST = "BACKTEST"

class Config:   
    """
    Configuration manager for setting up and managing the trading environment.

    This class orchestrates the initialization and setup of various components required for a trading session,
    including database connections, event queues, logging, and trading strategies. It supports both live and
    backtest modes and handles different components based on the selected mode.

    Attributes:
    - session_id (int): Identifier for the trading session.
    - mode (Mode): Operational mode of the trading session (e.g., LIVE, BACKTEST).
    - params (Parameters): Configuration parameters for the session.
    - event_queue (queue.Queue): Event queue for managing messages between components.
    - database (DatabaseClient): Client for database operations.
    - logger (logging.Logger): Configured logger for the trading session.
    - order_book (OrderBook): Manages orders during the session.
    - strategy (BaseStrategy): The trading strategy in use.
    - order_manager (OrderManager): Manages order execution and tracking.
    - portfolio_server (PortfolioServer): Manages portfolio states and valuations.
    - performance_manager (BasePerformanceManager): Tracks and reports on session performance.
    - risk_model (BaseRiskModel): Manages and assesses risk associated with the trading strategy.
    - db_updater (DatabaseUpdater): Manages database updates in response to various events.

    Methods:
    - setup(): Sets up the trading environment based on the mode and parameters.
    - map_symbol(symbol: Symbol): Maps ticker symbols to their respective data ticker.
    - load_live_data(): Loads live data for trading.
    - load_backtest_data(): Loads historical data for backtesting.
    - load_train_data(): Loads training data for strategy initialization.
    - set_strategy(strategy: Union[BaseStrategy, type]): Sets and initializes the trading strategy.

    Raises:
    - ValueError: If the `mode` or `params` are not of the expected type.
    """
    def __init__(self, session_id: int, mode: Mode, params: Parameters, database_key: str, database_url: str, risk_model: BaseRiskModel = None, logger_output="file", logger_level=logging.INFO):
        # User Variables
        self.session_id = session_id
        self.mode = mode
        self.params = params

        # Components
        self.event_queue = queue.Queue()
        self.database = DatabaseClient(database_key, database_url)
        self.logger = SystemLogger(params.strategy_name, output=logger_output, level=logger_level).logger
        self.order_book: OrderBook
        self.strategy: BaseStrategy = None
        self.order_manager: OrderManager
        self.portfolio_server: PortfolioServer
        self.performance_manager: BasePerformanceManager
        self.risk_model: BaseRiskModel
        self.db_updater: DatabaseUpdater = None
        self.live_data_client: LiveDataClient
        self.hist_data_client: HistoricalDataClient
        self.broker_client = None
        self.dummy_broker = None
        self.contract_handler: ContractManager
        self.eod_event_flag = None

        # Variables
        self.symbols_map: Dict[str, Symbol] = {}
        self.data_ticker_map = {}
        self.train_data : pd.DataFrame

        # Set-up
        self._set_risk_model(risk_model)
        self._map_symbols()

        # Initialize components based on mode
        if mode == Mode.LIVE:
            self.environment = LiveEnvironment(self)
        elif mode == Mode.BACKTEST:
            self.environment = BacktestEnvironment(self)
        
        self.environment.initialize_handlers()

    def _set_risk_model(self, risk_model: BaseRiskModel) -> None:
        """
        Instantiates the risk model and sets to the instance vaariabel if the user passes one.

        Parameters:
        - risk_model(BaseRiskModel | None): Risk model passed by user else defualt None.
        """
        if not risk_model or not issubclass(risk_model, BaseRiskModel):
            self.risk_model = None
            return
        self.risk_model = risk_model()

    def _map_symbols(self) -> None:
        """
        Maps a trading symbol to its respective ticker and stores in internal mappings.
        This method updates the internal dictionaries used for tracking symbols throughout the system.
        """
        # Map ticker to symbol object
        for symbol in self.params.symbols:
            self.data_ticker_map[symbol.data_ticker] = symbol.ticker
            self.symbols_map[symbol.ticker] = symbol

    def set_strategy(self, strategy: Union[BaseStrategy, type]):
        """
        Sets and initializes the trading strategy for the session.

        Parameters:
        - strategy (Union[BaseStrategy, type]): The strategy class to be used for trading.

        This method initializes the strategy with necessary data and configurations and attaches it to the trading system.
        It ensures that the strategy is properly integrated with other system components like the order book and portfolio manager.
        """
        # Check if 'strategy' is a class and a subclass of BaseStrategy
        if not isinstance(strategy, type) or not issubclass(strategy, BaseStrategy):
            raise ValueError(f"'strategy' must be a class and a subclass of BaseStrategy.")
        try:
            self.strategy = strategy(symbols_map= self.symbols_map, historical_data = self.train_data, portfolio_server=self.portfolio_server, logger = self.logger, order_book = self.order_book, event_queue=self.event_queue)
            self.performance_manager.set_strategy(self.strategy)
        except:
            raise RuntimeError("Error creating strategy instance.")

class BaseEnvironment(ABC):
    def __init__(self, config:Config):
        self.config = config

    def initialize_handlers(self):
        self.config.order_book = OrderBook(data_type=self.config.params.data_type, event_queue=self.config.event_queue)
        self.config.portfolio_server = PortfolioServer(self.config.symbols_map, self.config.logger, self.config.database)
        self.config.order_manager = OrderManager(self.config.symbols_map, self.config.event_queue, self.config.order_book, self.config.portfolio_server, self.config.logger)

    def _load_train_data(self):
        """
        Retrieves and formats historical data used for training the trading strategy.

        Loads the necessary historical data for the training period specified in the parameters. This data is essential for
        strategy initialization and calibration before live trading or detailed backtesting begins.
        """
        # Get historical data
        tickers = list(self.config.data_ticker_map.keys())
        self.config.hist_data_client.get_data(tickers, self.config.params.train_start, self.config.params.train_end, self.config.params.missing_values_strategy)
        train_data = self.config.hist_data_client.data

        # # Extract contract details for mapping
        contracts_map = {symbol.data_ticker: symbol.ticker for symbol in self.config.symbols_map.values()}
        train_data['symbol'] = train_data['symbol'].map(contracts_map)

        # # Sorting the DataFrame by the 'timestamp' column in ascending order
        self.config.train_data = train_data.sort_values(by='timestamp', ascending=True).reset_index(drop=True)

    @abstractmethod
    def _set_environment(self):
        pass

    @abstractmethod
    def _load_data(self):
        pass

class LiveEnvironment(BaseEnvironment):
    def __init__(self, config:Config):
        self.config = config

    def initialize_handlers(self):
        super().initialize_handlers()
        self._initialize_observer_patterns()
        self._set_environment()
        self._load_train_data()
        self._load_data()

    def _initialize_observer_patterns(self):
        """
        Configures observer patterns for updating database and managing risk based on trading events.

        This method attaches various components such as the database updater and risk model (if available)
        as observers to critical system events. This setup allows for seamless integration of data updates
        and risk management across the trading system components.
        """
        self.config.db_updater = DatabaseUpdater(self.config.database, self.config.session_id)
        
        # Attach the DatabaseUpdater as an observer to OrderBook and PortfolioServer
        self.config.order_book.attach(self.config.db_updater, EventType.MARKET_EVENT)
        self.config.portfolio_server.attach(self.config.db_updater, EventType.POSITION_UPDATE)
        self.config.portfolio_server.attach(self.config.db_updater, EventType.ORDER_UPDATE)
        self.config.portfolio_server.attach(self.config.db_updater, EventType.ACCOUNT_DETAIL_UPDATE)

        if self.config.risk_model:
            # Attach the DatabaseUpdater as an observer to RiskModel
            self.config.risk_model.attach(self.config.db_updater, EventType.RISK_MODEL_UPDATE)

            # Attach the risk model as an observer to OrderBook and PortfolioServer
            self.config.order_book.attach(self.config.risk_model, EventType.MARKET_EVENT)
            self.config.portfolio_server.attach(self.config.risk_model, EventType.POSITION_UPDATE)
            self.config.portfolio_server.attach(self.config.risk_model, EventType.ORDER_UPDATE)
            self.config.portfolio_server.attach(self.config.risk_model, EventType.ACCOUNT_DETAIL_UPDATE)

    def _set_environment(self):
        """
        Sets up the environment necessary for live trading, including performance management and live data and broker clients.

        This method initializes performance managers and gateways required for live trading. It ensures that all
        connections to live data feeds and brokerage services are established and operational before trading begins.
        """
        from midas.engine.performance.live import LivePerformanceManager
        from midas.engine.gateways.live import (DataClient, BrokerClient, ContractManager)
        from midas.engine.gateways.backtest import DataClient as HistoricalDataClient 
        
        # Performance
        self.config.performance_manager = LivePerformanceManager(self.config.database, self.config.logger, self.config.params)

        # Gateways
        self.config.hist_data_client = HistoricalDataClient(self.config.event_queue, self.config.database, self.config.order_book, self.config.eod_event_flag)
        self.config.live_data_client = DataClient(self.config.event_queue, self.config.order_book, self.config.logger)
        self.config.broker_client = BrokerClient(self.config.event_queue, self.config.logger, self.config.portfolio_server, self.config.performance_manager)
        self._connect_live_clients()
    
        # Contract Handler
        self.config.contract_handler = ContractManager(self.config.live_data_client, self.config.logger) # TODO: CAN ADD to the Data CLIENT AND/OR TRADE CLIENT

        for ticker, symbol in self.config.symbols_map.items():
            if not self.config.contract_handler.validate_contract(symbol.contract):
                raise RuntimeError(f"{ticker} invalid contract.")
            
    def _connect_live_clients(self):
        """
        Establishes connections with live data and brokerage service clients.
        """
        self.config.live_data_client.connect()
        self.config.broker_client.connect()

    def _load_data(self):
        """
        Loads and subscribes to live data feeds for the symbols in the trading strategy.

        This method sets up the data client connections and begins receiving real-time data, which is essential
        for live trading environments. It handles the dynamic connection to data sources and begins the data streaming
        to the system components.
        """
        try:
            for _, symbol in self.config.symbols_map.items():
                self.config.live_data_client.get_data(data_type=self.config.params.data_type, contract=symbol.contract) 
        except ValueError:
            raise ValueError(f"Error loading live data for symbol {symbol.ticker}.")

class BacktestEnvironment(BaseEnvironment):
    def __init__(self, config:Config):
        self.config = config

    def initialize_handlers(self):
        super().initialize_handlers()
        self._set_environment()
        self._load_train_data()
        self._load_data()

    def _set_environment(self):
        """
        Configures the environment for backtesting, including performance management and historical data clients.

        This setup provides all necessary components to simulate trading using historical data, allowing the system
        to test trading strategies under historical market conditions.
        """
        from midas.engine.performance.backtest import BacktestPerformanceManager
        from midas.engine.gateways.backtest import (DataClient, BrokerClient, DummyBroker)
        # EOD Event Handling
        self.config.eod_event_flag = threading.Event()

        # Performance
        self.config.performance_manager = BacktestPerformanceManager(self.config.database, self.config.logger, self.config.params)

        # Gateways
        self.config.hist_data_client = DataClient(self.config.event_queue, self.config.database, self.config.order_book, self.config.eod_event_flag)
        self.config.dummy_broker = DummyBroker(self.config.symbols_map, self.config.event_queue, self.config.order_book, self.config.params.capital, self.config.logger)
        self.config.broker_client = BrokerClient(self.config.event_queue, self.config.logger, self.config.portfolio_server, self.config.performance_manager, self.config.dummy_broker, self.config.eod_event_flag)
        
    def _load_data(self):
        """
        Loads historical data for the period specified in the parameters for backtesting.

        Retrieves and processes historical data needed to simulate trading in a backtest environment. This data is used
        to feed into the system as if it were live, allowing the strategy to make decisions based on historical market conditions.
        """
        tickers = list(self.config.data_ticker_map.keys())
        response = self.config.hist_data_client.get_data(tickers, self.config.params.test_start, self.config.params.test_end,self.config.params.missing_values_strategy)

        if response:
            self.config.logger.info(f"Backtest data loaded.")
        else:
            raise RuntimeError("Backtest data did not load.")
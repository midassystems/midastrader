import queue
import logging
from enum import Enum
from typing import Union
from decouple import config

from .parameters import Parameters
from midas.engine.observer import EventType
from midas.engine.order_book import OrderBook
from midas.engine.strategies import BaseStrategy
from midas.engine.risk_model import BaseRiskModel
from midas.engine.data_sync import DatabaseUpdater
from midas.engine.portfolio import PortfolioServer
from midas.engine.order_manager import OrderManager
from midas.engine.performance import BasePerformanceManager

from midas.client import DatabaseClient

from midas.shared.symbol import Symbol
from midas.shared.utils.logger import SystemLogger

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

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
    def __init__(self, session_id: int,mode: Mode, params: Parameters, risk_model: BaseRiskModel = None, logger_output="file", logger_level=logging.INFO):
        if not isinstance(mode, Mode):
            raise ValueError(f"'mode' must be of type Mode enum.")
        
        if not isinstance(params, Parameters):
            raise ValueError(f"'params' must be of type Parameters instance.")
        
        self.session_id = session_id
        self.mode = mode
        self.params = params
        self.event_queue = queue.Queue()
        self.database = DatabaseClient(DATABASE_KEY, DATABASE_URL)
        self.logger = SystemLogger(params.strategy_name, output=logger_output, level=logger_level).logger

        # Handlers
        self.order_book: OrderBook
        self.strategy: BaseStrategy
        self.order_manager: OrderManager
        self.portfolio_server: PortfolioServer
        self.performance_manager: BasePerformanceManager
        self.risk_model: BaseRiskModel
        self.db_updater: DatabaseUpdater = None

        if risk_model:
            self.risk_model = risk_model()
        else:
            self.risk_model = None

        # Variables
        self.live_data_client = None
        self.hist_data_client = None
        self.broker_client = None
        self.dummy_broker = None
        self.contract_handler = None
        self.symbols_map = {}
        self.data_ticker_map = {}

        # Set-up
        self.setup()

    def setup(self):
        """
        Configures the initial environment for the trading session.

        This method maps ticker symbols to their respective symbols, initializes trading components,
        and pre-loads necessary data based on the operational mode. It sets up data subscriptions for live data or loads
        historical data for backtesting, based on the 'mode' attribute.
        """
        # Map ticker to symbol object
        for symbol in self.params.symbols:
            self.map_symbol(symbol)

        # Initialize components
        self._initialize_components()

        # Load historical data if the strategy requires a train period
        if self.params.train_start:
            self.load_train_data()

        # Set-up data subscriptions based on mode
        if self.mode == Mode.LIVE:
            self.load_live_data()
        elif self.mode == Mode.BACKTEST:
            self.load_backtest_data()

    def map_symbol(self, symbol: Symbol):
        """
        Maps a trading symbol to its respective ticker and stores in internal mappings.

        Parameters:
        - symbol (Symbol): The symbol object that contains both ticker and data ticker.

        This method updates the internal dictionaries used for tracking symbols throughout the system.
        """
        self.data_ticker_map[symbol.data_ticker] = symbol.ticker
        self.symbols_map[symbol.ticker] = symbol

    def _initialize_components(self):
        """
        Initializes core components of the trading system including the order book, portfolio server, and order manager.

        Based on the operational mode specified during initialization (live or backtest), this method sets up
        the appropriate environment by initializing observer patterns and setting up the live or backtest environment accordingly.
        This ensures that all necessary components are ready and configured before the trading activities start.
        """
        self.order_book = OrderBook(data_type=self.params.data_type, event_queue=self.event_queue)
        self.portfolio_server = PortfolioServer(self.symbols_map, self.logger, self.database)
        self.order_manager = OrderManager(self.symbols_map, self.event_queue, self.order_book, self.portfolio_server, self.logger)

        if self.mode == Mode.LIVE:
            self._initialize_observer_patterns()
            self._set_live_environment()
        elif self.mode == Mode.BACKTEST:
            self._set_backtest_environment()

    def _initialize_observer_patterns(self):
        """
        Configures observer patterns for updating database and managing risk based on trading events.

        This method attaches various components such as the database updater and risk model (if available)
        as observers to critical system events. This setup allows for seamless integration of data updates
        and risk management across the trading system components.
        """
        self.db_updater = DatabaseUpdater(self.database, self.session_id)
        
        # Attach the DatabaseUpdater as an observer to OrderBook and PortfolioServer
        self.order_book.attach(self.db_updater, EventType.MARKET_EVENT)
        self.portfolio_server.attach(self.db_updater, EventType.POSITION_UPDATE)
        self.portfolio_server.attach(self.db_updater, EventType.ORDER_UPDATE)
        self.portfolio_server.attach(self.db_updater, EventType.ACCOUNT_DETAIL_UPDATE)

        if self.risk_model:
            # Attach the DatabaseUpdater as an observer to RiskModel
            self.risk_model.attach(self.db_updater, EventType.RISK_MODEL_UPDATE)

            # Attach the risk model as an observer to OrderBook and PortfolioServer
            self.order_book.attach(self.risk_model, EventType.MARKET_EVENT)
            self.portfolio_server.attach(self.risk_model, EventType.POSITION_UPDATE)
            self.portfolio_server.attach(self.risk_model, EventType.ORDER_UPDATE)
            self.portfolio_server.attach(self.risk_model, EventType.ACCOUNT_DETAIL_UPDATE)

    def _set_live_environment(self):
        """
        Sets up the environment necessary for live trading, including performance management and live data and broker clients.

        This method initializes performance managers and gateways required for live trading. It ensures that all
        connections to live data feeds and brokerage services are established and operational before trading begins.
        """
        from midas.engine.performance.live import LivePerformanceManager
        from midas.engine.gateways.live import (DataClient, BrokerClient, ContractManager)
        
        # Performance
        self.performance_manager = LivePerformanceManager(self.database, self.logger, self.params)

        # Gateways
        self.live_data_client = DataClient(self.event_queue, self.order_book, self.logger)
        self.broker_client = BrokerClient(self.event_queue, self.logger, self.portfolio_server, self.performance_manager)
        self._connect_live_clients()
    
        # Contract Handler
        self.contract_handler = ContractManager(self.live_data_client, self.logger) # TODO: CAN ADD to the Data CLIENT AND/OR TRADE CLIENT

        for ticker, symbol in self.symbols_map.items():
            if not self.contract_handler.validate_contract(symbol.contract):
                raise RuntimeError(f"{ticker} invalid contract.")

    def _set_backtest_environment(self):
        """
        Configures the environment for backtesting, including performance management and historical data clients.

        This setup provides all necessary components to simulate trading using historical data, allowing the system
        to test trading strategies under historical market conditions.
        """
        from midas.engine.performance.backtest import BacktestPerformanceManager
        from midas.engine.gateways.backtest import (DataClient, BrokerClient, DummyBroker)

        # Performance
        self.performance_manager = BacktestPerformanceManager(self.database, self.logger, self.params)

        # Gateways
        self.hist_data_client = DataClient(self.event_queue, self.database, self.order_book)
        self.dummy_broker = DummyBroker(self.symbols_map, self.event_queue, self.order_book, self.params.capital, self.logger)
        self.broker_client = BrokerClient(self.event_queue, self.logger, self.portfolio_server, self.performance_manager, self.dummy_broker)
        
    def _connect_live_clients(self):
        """
        Establishes connections with live data and brokerage service clients.
        """
        self.live_data_client.connect()
        self.broker_client.connect()

    def load_live_data(self):
        """
        Loads and subscribes to live data feeds for the symbols in the trading strategy.

        This method sets up the data client connections and begins receiving real-time data, which is essential
        for live trading environments. It handles the dynamic connection to data sources and begins the data streaming
        to the system components.
        """
        try:
            for _, symbol in self.symbols_map.items():
                self.live_data_client.get_data(data_type=self.params.data_type, contract=symbol.contract) 
        except ValueError:
            raise ValueError(f"Error loading live data for symbol {symbol.ticker}.")

    def load_backtest_data(self):
        """
        Loads historical data for the period specified in the parameters for backtesting.

        Retrieves and processes historical data needed to simulate trading in a backtest environment. This data is used
        to feed into the system as if it were live, allowing the strategy to make decisions based on historical market conditions.
        """
        tickers = list(self.data_ticker_map.keys())
        response  = self.hist_data_client.get_data(tickers, self.params.test_start, self.params.test_end,self.params.missing_values_strategy)

        if response:
            self.logger.info(f"Backtest data loaded.")
        else:
            raise RuntimeError("Backtest data did not load.")

    def load_train_data(self):
        """
        Retrieves and formats historical data used for training the trading strategy.

        Loads the necessary historical data for the training period specified in the parameters. This data is essential for
        strategy initialization and calibration before live trading or detailed backtesting begins.
        """
        # If live the dataclient from teh backtest need to get historical dat
        if not self.hist_data_client:
            from engine.gateways.backtest import (DataClient)
            self.hist_data_client = DataClient(self.event_queue, self.database, self.order_book)

        # Get historical data
        tickers = list(self.data_ticker_map.keys())
        self.hist_data_client.get_data(tickers, self.params.train_start, self.params.train_end, self.params.missing_values_strategy)
        train_data = self.hist_data_client.data

        # # Extract contract details for mapping
        contracts_map = {symbol.data_ticker: symbol.ticker for symbol in self.symbols_map.values()}
        train_data['symbol'] = train_data['symbol'].map(contracts_map)

        # # Sorting the DataFrame by the 'timestamp' column in ascending order
        train_data = train_data.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        self.train_data = train_data.pivot(index='timestamp', columns='symbol', values='close')

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
            self.strategy = strategy(symbols_map= self.symbols_map, train_data = self.train_data, portfolio_server=self.portfolio_server, logger = self.logger, order_book = self.order_book, event_queue=self.event_queue)
            
        except:
            raise RuntimeError("Error creating strategy instance.")
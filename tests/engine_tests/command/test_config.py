import random
import threading
import unittest
import pandas as pd
from contextlib import ExitStack
from unittest.mock import Mock, patch

from midas.engine.observer import EventType
from midas.engine.order_book import OrderBook
from midas.engine.strategies import BaseStrategy
from midas.engine.portfolio import PortfolioServer
from midas.engine.data_sync import DatabaseUpdater
from midas.engine.order_manager import OrderManager
from midas.shared.market_data import MarketDataType
from midas.engine.command.parameters import Parameters
from midas.engine.gateways.backtest import DummyBroker
from midas.engine.risk import BaseRiskModel, RiskHandler
from midas.engine.performance.live import LivePerformanceManager
from midas.engine.gateways.live import DataClient as LiveDataClient
from midas.engine.gateways.live import BrokerClient as LiveBrokerClient 
from midas.engine.performance.backtest import BacktestPerformanceManager
from midas.engine.gateways.backtest import DataClient as HistoricalDataClient
from midas.engine.gateways.backtest import BrokerClient  as BacktestBrokerClient
from midas.shared.symbol import Future, Currency, Venue, Industry, ContractUnits, Currency
from midas.engine.command.config import Config, Mode, BacktestEnvironment, LiveEnvironment


DATABASE_KEY = "MIDAS_API_KEY"
DATABASE_URL = "MIDAS_URL"

class TestRiskModel(BaseRiskModel):
    def __init__(self):
        pass

    def evaluate_risk(self, data: dict) -> dict:
        pass

class TestStrategy(BaseStrategy):
    def __init__(self, symbols_map, historical_data, portfolio_server, logger, order_book,event_queue):
        pass
    def prepare(self):
        pass 
    def _asset_allocation(self):
        pass
    def _entry_signal(self):
        pass
    def _exit_signal(self):
        pass
    def handle_market_data(self):
        pass

    def get_strategy_data(self) -> pd.DataFrame:
        pass

class TestConfig(unittest.TestCase):   
    def setUp(self) -> None:
        # Test symbols objects
        self.symbols = [
            Future(ticker = "HE",
                data_ticker = "HE.n.0",
                currency = Currency.USD,  
                exchange = Venue.CME,  
                fees = 0.85,  
                initial_margin =4564.17,
                quantity_multiplier=40000,
                price_multiplier=0.01,
                product_code="HE",
                product_name="Lean Hogs",
                industry=Industry.AGRICULTURE,
                contract_size=40000,
                contract_units=ContractUnits.POUNDS,
                tick_size=0.00025,
                min_price_fluctuation=10,
                continuous=False,
                lastTradeDateOrContractMonth="202404"),
            Future(ticker = "ZC",
                data_ticker = "ZC.n.0",
                currency = Currency.USD,  
                exchange = Venue.CBOT,  
                fees = 0.85,  
                initial_margin =2056.75,
                quantity_multiplier=40000,
                price_multiplier=0.01,
                product_code="ZC",
                product_name="Corn",
                industry=Industry.AGRICULTURE,
                contract_size=5000,
                contract_units=ContractUnits.BUSHELS,
                tick_size=0.0025,
                min_price_fluctuation=10,
                continuous=False,
                lastTradeDateOrContractMonth="202406")
        ]
        
        # Test parameters object
        self.params = Parameters(strategy_name = "Testing",
                            capital = 1000000,
                            data_type = random.choice([MarketDataType.BAR, MarketDataType.QUOTE]),
                            missing_values_strategy = random.choice(['drop', 'fill_forward']),
                            train_start =  "2023-05-18",
                            train_end = "2023-12-31",
                            test_start = "2024-01-01",
                            test_end = "2024-01-19",
                            symbols = self.symbols)

    # Basic Validation 
    def test_set_risk_model(self):
        mode = Mode.LIVE

        # Test
        with ExitStack() as stack:
            mock_backtest_env = stack.enter_context(patch.object(LiveEnvironment, 'initialize_handlers'))

            # Initialize Config
            config = Config(
                session_id=10897,
                mode=mode,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )
            
            # Mock Methods
            config.portfolio_server= Mock()
            config.order_book = Mock()

            # Test
            config.set_risk_model(TestRiskModel)

        # Validate
        self.assertIsInstance(config.risk_handler,RiskHandler)
        mock_backtest_env.assert_called_once()

    def test_set_risk_model_null(self):
        mode = Mode.LIVE

        # Test
        with ExitStack() as stack:
            mock_live_env = stack.enter_context(patch.object(LiveEnvironment, 'initialize_handlers'))

            # Initialize Config
            config = Config(
                session_id=10897,
                mode=mode,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )

        # Validate
        self.assertEqual(config.risk_handler, None)
        mock_live_env.assert_called_once()

    def test_symbols_map(self):
        mode = Mode.BACKTEST

        # Test
        with ExitStack() as stack:
            mock_live_env = stack.enter_context(patch.object(LiveEnvironment, 'initialize_handlers'))
            mock_backtest_env = stack.enter_context(patch.object(BacktestEnvironment, 'initialize_handlers'))

            # Initialize Config
            config = Config(
                session_id=10897,
                mode=mode,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )

        # Validate
        for symbol in self.symbols:
            self.assertEqual(config.data_ticker_map[symbol.data_ticker], symbol.ticker) 
            self.assertEqual(config.symbols_map[symbol.ticker], symbol) 

    def test_set_strategy_clean(self):
        mode = Mode.BACKTEST
        
        # Test
        with ExitStack() as stack:
            mock_live_env = stack.enter_context(patch.object(LiveEnvironment, 'initialize_handlers'))
            mock_backtest_env = stack.enter_context(patch.object(BacktestEnvironment, 'initialize_handlers'))

            # Initialize Config
            config = Config(
                session_id=10897,
                mode=mode,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )
            config.train_data = Mock()
            config.portfolio_server= Mock()
            config.order_book = Mock()
            config.performance_manager = Mock()

            # Test
            config.set_strategy(TestStrategy)
            
        # Validate
        self.assertIsInstance(config.strategy, TestStrategy)

    def test_set_strategy_exceptiom(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_backtest_env = stack.enter_context(patch.object(BacktestEnvironment, 'initialize_handlers'))

            # Initialize Config
            config = Config(
                session_id=10897,
                mode=mode,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )

            # Test
            with self.assertRaisesRegex(RuntimeError, "Error creating strategy instance."): 
                config.set_strategy(BaseStrategy)

    def test_setup_live(self):
        mode = Mode.LIVE
        
        with ExitStack() as stack:
            mock_live_env = stack.enter_context(patch.object(LiveEnvironment, 'initialize_handlers'))

            # Initialize Config
            config = Config(
                session_id=10897,
                mode=mode,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )

            # Validate
            mock_live_env.assert_called_once()

    def test_setup_backtest(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_live_env = stack.enter_context(patch.object(LiveEnvironment, 'initialize_handlers'))
            mock_backtest_env = stack.enter_context(patch.object(BacktestEnvironment, 'initialize_handlers'))

            # Initialize Config
            config = Config(
                session_id=10897,
                mode=mode,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )

            # Validate
            mock_backtest_env.assert_called_once()

class TestBacktestEnvironment(unittest.TestCase):
    def setUp(self) -> None:
        # Test symbols objects
        self.symbols = [
            Future(ticker = "HE",
                data_ticker = "HE.n.0",
                currency = Currency.USD,  
                exchange = Venue.CME,  
                fees = 0.85,  
                initial_margin =4564.17,
                quantity_multiplier=40000,
                price_multiplier=0.01,
                product_code="HE",
                product_name="Lean Hogs",
                industry=Industry.AGRICULTURE,
                contract_size=40000,
                contract_units=ContractUnits.POUNDS,
                tick_size=0.00025,
                min_price_fluctuation=10,
                continuous=False,
                lastTradeDateOrContractMonth="202404"),
            Future(ticker = "ZC",
                data_ticker = "ZC.n.0",
                currency = Currency.USD,  
                exchange = Venue.CBOT,  
                fees = 0.85,  
                initial_margin =2056.75,
                quantity_multiplier=40000,
                price_multiplier=0.01,
                product_code="ZC",
                product_name="Corn",
                industry=Industry.AGRICULTURE,
                contract_size=5000,
                contract_units=ContractUnits.BUSHELS,
                tick_size=0.0025,
                min_price_fluctuation=10,
                continuous=False,
                lastTradeDateOrContractMonth="202406")
        ]
        
        # Test parameters object
        self.params = Parameters(strategy_name = "Testing",
                            capital = 1000000,
                            data_type = random.choice([MarketDataType.BAR, MarketDataType.QUOTE]),
                            missing_values_strategy = random.choice(['drop', 'fill_forward']),
                            train_start =  "2023-05-18",
                            train_end = "2023-12-31",
                            test_start = "2024-01-01",
                            test_end = "2024-01-19",
                            symbols = self.symbols)
        
        # Mock Instantiate Config
        mode = Mode.BACKTEST
        with ExitStack() as stack:
            self.init_handlers = stack.enter_context(patch.object(BacktestEnvironment, 'initialize_handlers'))

            # Initialize Config
            self.config = Config(
                session_id=10897,
                mode=mode,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )

            # Create BacktestEnvironment object
            self.environment = BacktestEnvironment(self.config)
    
    def test_initialize_handlers(self):
        self.environment._set_environment = Mock()
        self.environment._load_train_data = Mock()
        self.environment._load_data = Mock()

        # Test
        self.environment.initialize_handlers()

        # Validate
        self.assertIsInstance(self.config.order_book, OrderBook)
        self.assertIsInstance(self.config.portfolio_server, PortfolioServer)
        self.assertIsInstance(self.config.order_manager, OrderManager)
        self.environment._set_environment.assert_called_once()
        self.environment._load_train_data.assert_called_once()
        self.environment._load_data.assert_called_once()

    def test_set_environment(self):
        self.config.order_book = Mock()
        self.config.portfolio_server = Mock()
        self.config.order_manager = Mock()
        
        # Test
        self.environment._set_environment()

        # Validate
        self.assertIsInstance(self.config.performance_manager, BacktestPerformanceManager)
        self.assertIsInstance(self.config.hist_data_client, HistoricalDataClient)
        self.assertIsInstance(self.config.dummy_broker, DummyBroker)
        self.assertIsInstance(self.config.broker_client, BacktestBrokerClient)
        self.assertIsInstance(self.config.eod_event_flag,threading.Event)

    def test_load_data(self):
        self.config.hist_data_client = Mock()
        self.config.logger = Mock()
        self.config.hist_data_client.get_data = Mock(return_value = True) 

        # Test
        self.environment._load_data()

        # Validate
        self.config.hist_data_client.get_data.assert_called_once()
        self.config.logger.info.assert_called_once_with(f"Backtest data loaded.")
   
    def test_load_train_data(self):
        # Create mock df 
        data = {
            'timestamp': [
                1684414800000000000, 1684414800000000000, 1684418400000000000,
                1684418400000000000, 1703872800000000000, 1703872800000000000, 1703876400000000000,
                1703876400000000000
            ],
            'symbol': [
                'HE.n.0', 'ZC.n.0', 'HE.n.0', 'ZC.n.0',
                  'HE.n.0', 'ZC.n.0', 'HE.n.0', 'ZC.n.0'
            ],
            'open': [
                85.0750, 551.0000, 84.8000, 557.2500, 68.1000, 471.2500, 67.9750, 471.5000
            ],
            'close': [
                84.8500, 557.2500, 85.1500, 553.5000, 68.0000, 471.5000, 68.2750, 470.7500
            ],
            'high': [
                85.2500, 557.2500, 86.0000, 559.2500, 68.1500, 472.0000, 68.3500, 471.7500
            ],
            'low': [
                83.3000, 547.0000, 84.7750, 553.0000, 67.9250, 471.2500, 67.9750, 470.5000
            ],
            'volume': [
                3978, 24363, 1808, 20583, 3019, 8174, 554, 11980
            ]
        }
        mock_df = pd.DataFrame(data)
        
        # Mock methods
        self.config.hist_data_client = Mock()
        self.config.hist_data_client.get_data = Mock()
        self.config.hist_data_client.data = mock_df

        # Test
        self.environment._load_train_data()

        # Expected
        data["symbol"] = [
                'HE', 'ZC', 'HE', 'ZC',
                  'HE', 'ZC', 'HE', 'ZC'
        ]
        expected_df = pd.DataFrame(data)

        # Validate
        pd.testing.assert_frame_equal(self.config.train_data, expected_df)

class TestLiveEnvironment(unittest.TestCase):
    def setUp(self) -> None:
        # Test sybmol objects
        self.symbols = [
            Future(ticker = "HE",
                data_ticker = "HE.n.0",
                currency = Currency.USD,  
                exchange = Venue.CME,  
                fees = 0.85,  
                initial_margin =4564.17,
                quantity_multiplier=40000,
                price_multiplier=0.01,
                product_code="HE",
                product_name="Lean Hogs",
                industry=Industry.AGRICULTURE,
                contract_size=40000,
                contract_units=ContractUnits.POUNDS,
                tick_size=0.00025,
                min_price_fluctuation=10,
                continuous=False,
                lastTradeDateOrContractMonth="202404"),
            Future(ticker = "ZC",
                data_ticker = "ZC.n.0",
                currency = Currency.USD,  
                exchange = Venue.CBOT,  
                fees = 0.85,  
                initial_margin =2056.75,
                quantity_multiplier=40000,
                price_multiplier=0.01,
                product_code="ZC",
                product_name="Corn",
                industry=Industry.AGRICULTURE,
                contract_size=5000,
                contract_units=ContractUnits.BUSHELS,
                tick_size=0.0025,
                min_price_fluctuation=10,
                continuous=False,
                lastTradeDateOrContractMonth="202406")
        ]
        
        # Test parameter objet
        self.params = Parameters(strategy_name = "Testing",
                            capital = 1000000,
                            data_type = random.choice([MarketDataType.BAR, MarketDataType.QUOTE]),
                            missing_values_strategy = random.choice(['drop', 'fill_forward']),
                            train_start =  "2023-05-18",
                            train_end = "2023-12-31",
                            test_start = "2024-01-01",
                            test_end = "2024-01-19",
                            symbols = self.symbols)
        
        with ExitStack() as stack:
            self.init_handlers = stack.enter_context(patch.object(LiveEnvironment, 'initialize_handlers'))

            # Initialize Config
            self.config = Config(
                session_id=10897,
                mode=Mode.LIVE,
                params=self.params,
                database_key=DATABASE_KEY,
                database_url=DATABASE_URL,
                output_path="./tests/outputs/"
            )

            self.environment = LiveEnvironment(self.config)
    
    def test_initialize_handlers(self):
        self.environment._set_environment = Mock()
        self.environment._load_train_data = Mock()
        self.environment._load_data = Mock()
        self.environment._initialize_observer_patterns = Mock()

        # Test
        self.environment.initialize_handlers()

        # Validate
        self.assertIsInstance(self.config.order_book, OrderBook)
        self.assertIsInstance(self.config.portfolio_server, PortfolioServer)
        self.assertIsInstance(self.config.order_manager, OrderManager)
        self.environment._set_environment.assert_called_once()
        self.environment._load_train_data.assert_called_once()
        self.environment._load_data.assert_called_once()
        self.environment._initialize_observer_patterns.assert_called_once() 

    def test_set_environment(self):
        from midas.engine.gateways.live import ContractManager

        self.config.order_book = Mock()
        self.config.portfolio_server = Mock()
        self.config.order_manager = Mock()
        self.environment._connect_live_clients = Mock()
        self.config.contract_handler = Mock()

        # Test
        with ExitStack() as stack:
            contract_handler = stack.enter_context(patch.object(ContractManager, 'validate_contract', return_value=True))

            self.environment._set_environment()

        # Validate
        self.assertIsInstance(self.config.performance_manager, LivePerformanceManager)
        self.assertIsInstance(self.config.hist_data_client, HistoricalDataClient)
        self.assertIsInstance(self.config.live_data_client, LiveDataClient)
        self.assertIsInstance(self.config.broker_client, LiveBrokerClient)
        self.assertEqual(self.config.eod_event_flag,None)

    def test_load_data(self):
        self.config.live_data_client = Mock()
        self.config.live_data_client.get_data = Mock() 

        # Test
        self.environment._load_data()

        # Validate
        self.assertEqual(self.config.live_data_client.get_data.call_count, len(self.symbols))
   
    def test_load_train_data(self):
        # Mock dataframe
        data = {
            'timestamp': [
                1684414800000000000, 1684414800000000000, 1684418400000000000,
                1684418400000000000, 1703872800000000000, 1703872800000000000, 1703876400000000000,
                1703876400000000000
            ],
            'symbol': [
                'HE.n.0', 'ZC.n.0', 'HE.n.0', 'ZC.n.0',
                  'HE.n.0', 'ZC.n.0', 'HE.n.0', 'ZC.n.0'
            ],
            'open': [
                85.0750, 551.0000, 84.8000, 557.2500, 68.1000, 471.2500, 67.9750, 471.5000
            ],
            'close': [
                84.8500, 557.2500, 85.1500, 553.5000, 68.0000, 471.5000, 68.2750, 470.7500
            ],
            'high': [
                85.2500, 557.2500, 86.0000, 559.2500, 68.1500, 472.0000, 68.3500, 471.7500
            ],
            'low': [
                83.3000, 547.0000, 84.7750, 553.0000, 67.9250, 471.2500, 67.9750, 470.5000
            ],
            'volume': [
                3978, 24363, 1808, 20583, 3019, 8174, 554, 11980
            ]
        }
        mock_df = pd.DataFrame(data)

        # Mock methods
        self.config.hist_data_client = Mock()
        self.config.hist_data_client.get_data = Mock()
        self.config.hist_data_client.data = mock_df

        # Test
        self.environment._load_train_data()

        # Expected
        data["symbol"] = [
                'HE', 'ZC', 'HE', 'ZC',
                  'HE', 'ZC', 'HE', 'ZC'
        ]
        expected_df = pd.DataFrame(data)

        # Validate
        pd.testing.assert_frame_equal(self.config.train_data, expected_df)

    def test_initialize_observer_patterns(self):
        self.config.order_book = Mock()
        self.config.portfolio_server = Mock()
        mock_db_updater = Mock()

        # Mock the __init__ to set the return value properly
        with patch.object(DatabaseUpdater, '__init__', side_effect=lambda *args, **kwargs: None):
            with patch('midas.engine.data_sync.database_updater.DatabaseUpdater') as MockDatabaseUpdater:
                MockDatabaseUpdater.return_value = mock_db_updater

                # Test
                self.environment._initialize_observer_patterns()

            # Validate
            self.config.order_book.attach.assert_called_with(self.config.db_updater,EventType.MARKET_EVENT)
            self.config.portfolio_server.attach.assert_any_call(self.config.db_updater, EventType.POSITION_UPDATE)
            self.config.portfolio_server.attach.assert_any_call(self.config.db_updater, EventType.ORDER_UPDATE)
            self.config.portfolio_server.attach.assert_any_call(self.config.db_updater, EventType.ACCOUNT_DETAIL_UPDATE)
        
    def test_initialize_risk_handler(self):
        self.config.order_book = Mock()
        self.config.portfolio_server = Mock()
        self.config.db_updater = Mock()

        # Test
        self.environment.initialize_risk_handler(TestRiskModel)

        # Validate
        self.assertIsInstance(self.config.risk_handler, RiskHandler)
        self.config.risk_handler.attach(self.config.db_updater, EventType.RISK_MODEL_UPDATE)
        self.config.order_book.attach.assert_called_with(self.config.risk_handler,EventType.MARKET_EVENT)
        self.config.portfolio_server.attach.assert_any_call(self.config.risk_handler, EventType.POSITION_UPDATE)
        self.config.portfolio_server.attach.assert_any_call(self.config.risk_handler, EventType.ORDER_UPDATE)
        self.config.portfolio_server.attach.assert_any_call(self.config.risk_handler, EventType.ACCOUNT_DETAIL_UPDATE)
    


if __name__ == "__main__":
    unittest.main()
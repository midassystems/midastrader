import random
import unittest
import pandas as pd
from decouple import config
from contextlib import ExitStack
from unittest.mock import Mock, patch
from pandas.testing import assert_frame_equal

from midas.engine.observer import EventType
from midas.engine.order_book import OrderBook
from midas.engine.strategies import BaseStrategy
from midas.engine.risk_model import BaseRiskModel
from midas.engine.portfolio import PortfolioServer
from midas.engine.order_manager import OrderManager
from midas.engine.command import Config, Mode, Parameters
from midas.engine.performance.live import LivePerformanceManager
from midas.engine.performance.backtest import BacktestPerformanceManager

from midas.client import DatabaseClient

from midas.shared.market_data import MarketDataType
from midas.shared.symbol import Future, Currency, Venue, Industry, ContractUnits, Currency

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')


#TODO: edge cases
class TestConfig(unittest.TestCase):   
    @classmethod
    def setUpClass(cls) -> None:
        cls.db_client=DatabaseClient(DATABASE_KEY, DATABASE_URL) 

    def setUp(self) -> None:
        self.valid_symbols = [
            Future(ticker = "HE",
                data_ticker = "HE.n.0",
                currency = Currency.USD,  
                exchange = Venue.CME,  
                fees = 0.85,  
                initialMargin =4564.17,
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
                initialMargin =2056.75,
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
        self.params = Parameters(strategy_name = "Testing",
                            capital = 1000000,
                            data_type = random.choice([MarketDataType.BAR, MarketDataType.QUOTE]),
                            missing_values_strategy = random.choice(['drop', 'fill_forward']),
                            train_start =  "2020-05-18",
                            train_end = "2023-12-31",
                            test_start = "2024-01-01",
                            test_end = "2024-01-19",
                            symbols = self.valid_symbols)

    # Basic Validation
    def test_live_connects(self):
        mode = Mode.LIVE
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(11, mode, self.params,DATABASE_KEY, DATABASE_URL, logger_output='terminal')
            self.config.live_data_client = Mock()
            self.config.broker_client = Mock()
            
            # Test
            self.config._connect_live_clients()

            # Validation
            self.config.live_data_client.connect.assert_called_once() # connect live data
            self.config.broker_client.connect.assert_called_once() # connect broker 

    def test_set_live_environment(self):
        from midas.engine.gateways.live import (DataClient, BrokerClient, ContractManager)
        
        mode = Mode.LIVE
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            mock_connect_live = stack.enter_context(patch.object(Config, '_connect_live_clients'))
            self.config = Config(111, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.portfolio_server = Mock() 
            self.config.performance_manager = Mock() 
            self.config.order_book = Mock() 
            
            # Test
            self.config._set_live_environment()

            # Validation
            self.assertIsInstance(self.config.performance_manager, LivePerformanceManager) # check performance manager is correct instance
            self.assertIsInstance(self.config.live_data_client, DataClient) # check live data client is correct instance
            self.assertIsInstance(self.config.broker_client, BrokerClient) # check broker client is correct instance
            self.assertIsInstance(self.config.contract_handler, ContractManager) # check contract manager is correct instance
            mock_connect_live.assert_called_once() # check _connect_live method called
    
    def test_set_backtest_environment(self):
        from midas.engine.gateways.backtest import (DataClient, BrokerClient, DummyBroker)
        
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(123,mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.portfolio_server = Mock() 
            self.config.performance_manager = Mock() 
            self.config.order_book = Mock()
            
            # Test
            self.config._set_backtest_environment()

            # Validation
            self.assertIsInstance(self.config.performance_manager, BacktestPerformanceManager) # check performance manager is correct instance
            self.assertIsInstance(self.config.hist_data_client, DataClient) # check live data client is correct instance
            self.assertIsInstance(self.config.broker_client, BrokerClient) # check broker client is correct instance
            self.assertIsInstance(self.config.dummy_broker, DummyBroker) # check dummy broker is correct instance

    def test_initialize_observer_patterns(self):
        mode = Mode.LIVE
        session_id=27852
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            mock_set_live_environment = stack.enter_context(patch.object(Config, '_set_live_environment'))
            self.config = Config(session_id, mode, self.params, DATABASE_KEY, DATABASE_URL)

            # Test
            self.config._initialize_components()

            # Validation
            self.assertEqual(self.config.order_book._observers, {EventType.MARKET_EVENT : [self.config.db_updater]})
            self.assertEqual(self.config.portfolio_server._observers, {EventType.POSITION_UPDATE : [self.config.db_updater], EventType.ACCOUNT_DETAIL_UPDATE : [self.config.db_updater], EventType.ORDER_UPDATE : [self.config.db_updater]})

            # clean  up
            self.db_client.delete_session(session_id)

    def test_initialize_observer_patterns_with_risk_model(self):
        mode = Mode.LIVE
        session_id =23453

        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            mock_set_live_environment = stack.enter_context(patch.object(Config, '_set_live_environment'))
            self.config = Config(session_id, mode, self.params, DATABASE_KEY, DATABASE_URL, BaseRiskModel)

            # Test
            self.config._initialize_components()

            # Validation
            self.assertEqual(self.config.order_book._observers, {EventType.MARKET_EVENT : [self.config.db_updater, self.config.risk_model]})
            self.assertEqual(self.config.portfolio_server._observers, {EventType.POSITION_UPDATE : [self.config.db_updater, self.config.risk_model], EventType.ACCOUNT_DETAIL_UPDATE : [self.config.db_updater, self.config.risk_model], EventType.ORDER_UPDATE : [self.config.db_updater, self.config.risk_model]})
            
            # clean  up
            self.db_client.delete_session(session_id)

    def test_initialize_components_live(self):
        mode = Mode.LIVE
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            mock_set_live_environment = stack.enter_context(patch.object(Config, '_set_live_environment'))
            mock_initialize_observer_patterns = stack.enter_context(patch.object(Config, '_initialize_observer_patterns'))
            self.config = Config(165, mode, self.params, DATABASE_KEY, DATABASE_URL)

            # Test
            self.config._initialize_components()

            # Validation
            self.assertIsInstance(self.config.order_book, OrderBook) # check order_book is correct instance
            self.assertIsInstance(self.config.portfolio_server, PortfolioServer) # check portfolio server is correct instance
            self.assertIsInstance(self.config.order_manager, OrderManager) # check order manager is correct instance
            mock_initialize_observer_patterns.assert_called_once() 
            mock_set_live_environment.assert_called_once() # check _set_live_environments method called

    def test_initialize_components_backtest(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            mock_set_backtest_environment = stack.enter_context(patch.object(Config, '_set_backtest_environment'))
            self.config = Config(1345, mode, self.params, DATABASE_KEY, DATABASE_URL)

            # Test
            self.config._initialize_components()

            # Validation
            self.assertIsInstance(self.config.order_book, OrderBook) # check order_book is correct instance
            self.assertIsInstance(self.config.portfolio_server, PortfolioServer) # check portfolio server is correct instance
            self.assertIsInstance(self.config.order_manager, OrderManager) # check order manager is correct instance
            mock_set_backtest_environment.assert_called_once() # check _set_backtest_environments method called
           
    def test_symbols_map_backtest(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(10897, mode, self.params, DATABASE_KEY, DATABASE_URL)

            for symbol in self.valid_symbols:
                # Test
                self.config.map_symbol(symbol)

                # Validation
                self.assertEqual(self.config.data_ticker_map[symbol.data_ticker], symbol.ticker) # check data_ticker_map filled correctly
                self.assertEqual(self.config.symbols_map[symbol.ticker], symbol) # check symbols_map filled correctly
    
    def test_symbols_map_live(self):
        mode = Mode.LIVE
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1786, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.contract_handler = Mock()

            for symbol in self.valid_symbols:
                self.config.contract_handler.validate_contract(symbol.contract).return_value = True # mock contract validated correctly
                # Test
                self.config.map_symbol(symbol)
                
                # Validation
                self.assertEqual(self.config.data_ticker_map[symbol.data_ticker], symbol.ticker) # check data_ticker_map filled correctly
                self.assertEqual(self.config.symbols_map[symbol.ticker], symbol) # check symbols_map filled correctly

    def test_load_train_data_live(self):
        mode = Mode.LIVE

        valid_db_response = [{"id":49252,"timestamp":"2022-05-02T14:00:00Z","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                  {"id":49253,"timestamp":"2022-05-02T14:00:00Z","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                  {"id":49256,"timestamp":"2022-05-02T15:00:00Z","symbol":"ZC.n.0","open":"797.5000","close":"798.2500","high":"800.5000","low":"795.7500","volume":7173},
                                  {"id":49257,"timestamp":"2022-05-02T15:00:00Z","symbol":"HE.n.0","open":"103.8500","close":"105.8500","high":"106.6750","low":"103.7750","volume":3489},
                                  {"id":49258,"timestamp":"2022-05-02T16:00:00Z","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                  {"id":49259,"timestamp":"2022-05-02T16:00:00Z","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                  {"id":49262,"timestamp":"2022-05-02T17:00:00Z","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
                                  {"id":49263,"timestamp":"2022-05-02T17:00:00Z","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
        ]
        
        # Create Properly Processed data for hist_data_client.get_data call
        df = pd.DataFrame(valid_db_response)
        df.drop(columns=['id'], inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['timestamp'] = (df['timestamp'].astype('int64') // 1e9).astype('int')
        
        ohlcv_columns = ['open', 'high', 'low', 'close', 'volume']
        df[ohlcv_columns] = df[ohlcv_columns].astype(float)
        
        valid_processed_data = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)

        # Expected Data
        train_data = valid_processed_data.copy()
        contracts_map = {symbol.data_ticker: symbol.ticker for symbol in self.valid_symbols}
        train_data['symbol'] = train_data['symbol'].map(contracts_map)
        train_data = train_data.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        expected_train_data = train_data.pivot(index='timestamp', columns='symbol', values='close')
        

        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.hist_data_client = Mock()
            self.config.contract_handler = Mock()
            self.config.hist_data_client.data = valid_processed_data

            for symbol in self.valid_symbols:
                self.config.contract_handler.validate_contract(symbol.contract).return_value = True
                self.config.map_symbol(symbol)

            # Test
            self.config.load_train_data()

            # Validate
            assert_frame_equal(self.config.train_data, expected_train_data, check_dtype=True) # check train datamatches expected

    def test_load_train_data_backtest(self):
        mode = Mode.BACKTEST

        valid_db_response = [{"id":49252,"timestamp":"2022-05-02T14:00:00Z","symbol":"HE.n.0","open":"104.0250","close":"103.9250","high":"104.2500","low":"102.9500","volume":3553},
                                  {"id":49253,"timestamp":"2022-05-02T14:00:00Z","symbol":"ZC.n.0","open":"802.0000","close":"797.5000","high":"804.0000","low":"797.0000","volume":12195},
                                  {"id":49256,"timestamp":"2022-05-02T15:00:00Z","symbol":"ZC.n.0","open":"797.5000","close":"798.2500","high":"800.5000","low":"795.7500","volume":7173},
                                  {"id":49257,"timestamp":"2022-05-02T15:00:00Z","symbol":"HE.n.0","open":"103.8500","close":"105.8500","high":"106.6750","low":"103.7750","volume":3489},
                                  {"id":49258,"timestamp":"2022-05-02T16:00:00Z","symbol":"HE.n.0","open":"105.7750","close":"104.7000","high":"105.9500","low":"104.2750","volume":2146},
                                  {"id":49259,"timestamp":"2022-05-02T16:00:00Z","symbol":"ZC.n.0","open":"798.5000","close":"794.2500","high":"800.2500","low":"794.0000","volume":9443},
                                  {"id":49262,"timestamp":"2022-05-02T17:00:00Z","symbol":"ZC.n.0","open":"794.5000","close":"801.5000","high":"803.0000","low":"794.2500","volume":8135},
                                  {"id":49263,"timestamp":"2022-05-02T17:00:00Z","symbol":"HE.n.0","open":"104.7500","close":"105.0500","high":"105.2750","low":"103.9500","volume":3057},
        ]
        
        # Create Properly Processed data for hist_data_client.get_data call
        df = pd.DataFrame(valid_db_response)
        df.drop(columns=['id'], inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['timestamp'] = (df['timestamp'].astype('int64') // 1e9).astype('int')
        
        ohlcv_columns = ['open', 'high', 'low', 'close', 'volume']
        df[ohlcv_columns] = df[ohlcv_columns].astype(float)
        
        valid_processed_data = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)

        # Expected Data
        train_data = valid_processed_data.copy()
        contracts_map = {symbol.data_ticker: symbol.ticker for symbol in self.valid_symbols}
        train_data['symbol'] = train_data['symbol'].map(contracts_map)
        train_data = train_data.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
        expected_train_data = train_data.pivot(index='timestamp', columns='symbol', values='close')
        

        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.hist_data_client = Mock()
            self.config.contract_handler = Mock()
            self.config.hist_data_client.data = valid_processed_data

            for symbol in self.valid_symbols:
                self.config.contract_handler.validate_contract(symbol.contract).return_value = True
                self.config.map_symbol(symbol)

            # Test
            self.config.load_train_data()

            # Validate
            assert_frame_equal(self.config.train_data, expected_train_data, check_dtype=True) # check train datamatches expected

    def test_load_backtest_data(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.hist_data_client = Mock()
            self.config.logger = Mock()
            self.config.hist_data_client.get_data.return_value = True # mock a response indicating data return with no errors

            # Test
            self.config.load_backtest_data()

            # Validation
            self.config.logger.info.assert_called_once_with("Backtest data loaded.")

    def test_load_backtest_data_failure(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.hist_data_client = Mock()
            self.config.logger = Mock()
            self.config.hist_data_client.get_data.return_value = None # mock a response indicating problem with data retrieval

            # Test
            with self.assertRaisesRegex(RuntimeError, "Backtest data did not load."):
                self.config.load_backtest_data() 

    def test_load_live_data(self):
        mode = Mode.LIVE
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.live_data_client = Mock()
            self.config.contract_handler = Mock()
            
            # Map Symbols as would happen
            for symbol in self.valid_symbols:
                self.config.contract_handler.validate_contract(symbol.contract).return_value = True # mock a response indicating data return with no errors
                self.config.map_symbol(symbol)
            
            # Test
            self.config.load_live_data()
            
            # Validation
            self.assertEqual(self.config.live_data_client.get_data.call_count, len(self.valid_symbols)) # check a live data call to start stream for each symbol

    def test_load_live_data_failure(self):
        mode = Mode.LIVE
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.live_data_client = Mock()
            self.config.contract_handler = Mock()
            self.config.live_data_client.get_data.side_effect = ValueError() # mock error with the live data call

            # Map Symbols as would happen
            for symbol in self.valid_symbols:
                self.config.contract_handler.validate_contract(symbol.contract).return_value = True
                self.config.map_symbol(symbol)

            # Test
            with self.assertRaises(ValueError): # error raised on a error in live data call
                self.config.load_live_data()

    def test_set_strategy_clean(self):
        mode = Mode.BACKTEST

        # Strategies are subclasses of BaseStrategy
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
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
            self.config.symbols_map = {}
            self.config.train_data = Mock()
            self.config.portfolio_server= Mock()
            self.config.order_book = Mock()
            self.config.performance_manager = Mock()

            # Test
            self.config.set_strategy(TestStrategy)
            
            # Validation
            self.assertIsInstance(self.config.strategy, TestStrategy) # check strategy instantiated correctly

    def test_set_strategy_exceptiom(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)

            # Test
            with self.assertRaisesRegex(RuntimeError, "Error creating strategy instance."): # error raised if strategy not a subclass of BaseStrategy
                self.config.set_strategy(BaseStrategy)

    def test_setup_live(self):
        mode = Mode.LIVE
        
        with ExitStack() as stack:
            mock_init_components = stack.enter_context(patch.object(Config, '_initialize_components'))
            mock_map_symbols = stack.enter_context(patch.object(Config, 'map_symbol'))
            mock_load_train_data = stack.enter_context(patch.object(Config, 'load_train_data'))
            mock_load_live_data = stack.enter_context(patch.object(Config, 'load_live_data'))
            
            # Test (Config.setup is called in constructor)
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
                
            # Validation
            mock_init_components.assert_called_once() # check _initialize_components method called
            self.assertEqual(mock_map_symbols.call_count, len(self.valid_symbols)) # check symbols map call for each symbol
            mock_load_train_data.assert_called_once() # check _load_train_data method called
            mock_load_live_data.assert_called_once() # check _load_live_data method called

    def test_setup_backtest(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_init_components = stack.enter_context(patch.object(Config, '_initialize_components'))
            mock_map_symbols = stack.enter_context(patch.object(Config, 'map_symbol'))
            mock_load_train_data = stack.enter_context(patch.object(Config, 'load_train_data'))
            mock_load_backtest_data = stack.enter_context(patch.object(Config, 'load_backtest_data'))
            
            # Test (Config.setup is called in constructor)
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)
                
            # Validation
            mock_init_components.assert_called_once() # check _initialize_components method called
            self.assertEqual(mock_map_symbols.call_count, len(self.valid_symbols)) # check symbols map call for each symbol
            mock_load_train_data.assert_called_once() # check _load_train_data method called
            mock_load_backtest_data.assert_called_once() # check _load_backtest_data method called

    # Type Validation
    def test_initialize_components_invalid_mode(self):
        mode = 'test'
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))

            # Test
            with self.assertRaisesRegex(ValueError, f"'mode' must be of type Mode enum."): # check error raised if Mode enum not passed in construction
                self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)

    def test_initialize_components_invalid_params(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))

            # Test
            with self.assertRaisesRegex(ValueError, "'params' must be of type Parameters instance."): # check error raised if Parameters instance not passed at construction
                self.config = Config(1, mode, "self.params", DATABASE_KEY, DATABASE_URL)

    def test_set_strategy_invalid_type(self):
        mode = Mode.BACKTEST
        
        with ExitStack() as stack:
            mock_setup = stack.enter_context(patch.object(Config, 'setup'))
            self.config = Config(1, mode, self.params, DATABASE_KEY, DATABASE_URL)

            # Test
            with self.assertRaisesRegex(ValueError, "'strategy' must be a class and a subclass of BaseStrategy."): # check error raised if not subclass of BaseStrategy passed
                self.config.set_strategy('testing')

if __name__ == "__main__":
    unittest.main()
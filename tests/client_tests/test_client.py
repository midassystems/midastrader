import copy
import logging
import unittest
from decimal import Decimal
from decouple import config

from midas.shared.symbol import *
from midas.shared.market_data import *
from midas.client import DatabaseClient
from midas.shared.backtest import Backtest
from midas.client import AdminDatabaseClient
from midas.shared.regression import RegressionResults
from midas.shared.live_session import LiveTradingSession

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

class TestBarDataMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Database clients
        cls.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 
        cls.admin_client = AdminDatabaseClient(DATABASE_KEY, DATABASE_URL) 

        # Create details for test symbol 
        cls.admin_client.create_security_type(SecurityType.STOCK)
        cls.admin_client.create_currency(Currency.USD)
        cls.admin_client.create_venue(Venue.NASDAQ)
        cls.admin_client.create_industry(Industry.TECHNOLOGY)

        # Create test symbol
        cls.ticker="AAPL4"
        cls.equity = Equity(ticker="AAPL4",
                                security_type=SecurityType.STOCK,
                                company_name="Apple Inc.",
                                exchange=Venue.NASDAQ,
                                currency=Currency.USD,
                                industry=Industry.TECHNOLOGY,
                                market_cap=10000000000.99,
                                shares_outstanding=1937476363,
                                fees=0.1,
                                initial_margin=0,
                                quantity_multiplier=1,
                                price_multiplier=1)
        cls.symbol=cls.admin_client.create_symbol(cls.equity)

    def test_get_bar_data_w_ticker_and_dates(self):
        # Create bardata
        bar=BarData(ticker="AAPL4",
                    timestamp=np.uint64(1712400000000000000),
                    open=Decimal('99.9999'),
                    high=Decimal('100.9999'),
                    low=Decimal('100.9999'),
                    close=Decimal('100.9999'),
                    volume=np.uint64(100),
                    )
        self.admin_client.create_bar_data(bar)
        
        # Test
        tickers=[self.ticker]
        start_date="2020-01-01"
        end_date="2025-02-02"
        response=self.client.get_bar_data(tickers, start_date, end_date)

        # Valdiate
        self.assertGreaterEqual(len(response), 1)

    @classmethod
    def tearDownClass(cls) -> None:
        # Delete symbol details created in setup
        resources = [
            ("asset classes", cls.admin_client.get_asset_classes, cls.admin_client.delete_asset_class),
            ("security types", cls.admin_client.get_security_types, cls.admin_client.delete_security_type),
            ("venues", cls.admin_client.get_venues, cls.admin_client.delete_venue),
            ("currencies", cls.admin_client.get_currencies, cls.admin_client.delete_currency),
            ("industries", cls.admin_client.get_industries, cls.admin_client.delete_industry),
            ("contract units", cls.admin_client.get_contract_units, cls.admin_client.delete_contract_units)
        ]

        for name, getter, deleter in resources:
            try:
                items = getter()
                for item in items:
                    try:
                        deleter(item["id"])
                    except Exception as e:
                        pass
            except Exception as e:
                pass

        # Delete symbol created in setup
        def delete_symbol(symbol: Symbol):
            try:
                response = cls.admin_client.get_symbol_by_ticker(symbol.ticker)
                if len(response) == 0:
                    logging.debug(f"No symbol found for ticker {symbol.ticker}, nothing to delete.")
                elif len(response) == 1:
                    cls.admin_client.delete_symbol(response[0]['id'])
                    # Verify deletion
                    verification = cls.admin_client.get_symbol_by_ticker(symbol.ticker)
                    if len(verification) == 0:
                        logging.debug(f"Successfully deleted symbol with ticker {symbol.ticker}.")
                    else:
                        logging.error(f"Failed to delete symbol with ticker {symbol.ticker}, it still exists.")
                else:
                    logging.error(f"Multiple entries found for ticker {symbol.ticker}, not deleting.")
            except Exception as e:
                logging.error(f"Error deleting symbol for ticker {symbol.ticker}: {e}")

        delete_symbol(cls.equity)
    
class TestRegressionMethods(unittest.TestCase):
    def setUp(self) -> None:
        # Database client
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 

        # Create mock backtest
        self.parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": 1526601600000000000, 
                                "train_end": 1674086400000000000, 
                                "test_start": 1674086400000000000, 
                                "test_end": 1705622400000000000, 
                                "tickers": ["AAPL"], 
                                "benchmark": ["^GSPC"]
                            }
        self.static_stats = [{
                                "net_profit": 330.0, 
                                "total_fees": 40.0, 
                                "total_return": 0.33, 
                                "ending_equity": 1330.0, 
                                "max_drawdown": 0.0, 
                                "total_trades": 2, 
                                "num_winning_trades": 2, 
                                "num_lossing_trades": 0, 
                                "avg_win_percent": 0.45, 
                                "avg_loss_percent": 0, 
                                "percent_profitable": 1.0, 
                                "profit_and_loss": 0.0, 
                                "profit_factor": 0.0, 
                                "avg_trade_profit": 165.0, 
                                "sortino_ratio": 0.0
                            }]
        self.timeseries_stats =  [
                                {
                                    "timestamp": 1702141200000000000,
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.330", 
                                    "daily_benchmark_return": "0.00499"
                                },
                                {
                                    "timestamp": 1702227600000000000,
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.087", 
                                    "daily_benchmark_return": "0.009"
                                }
                            ]
        self.trades =  [{
                                "trade_id": 1, 
                                "leg_id": 1, 
                                "timestamp": 1672704000000000000, 
                                "ticker": "AAPL", 
                                "quantity": 4, 
                                "avg_price": 130.74, 
                                "trade_value": -522.96, 
                                "action": "BUY", 
                                "fees": 0.0
                            }]
        self.signals =  [{
                                "timestamp": 1672704000000000000, 
                                "trade_instructions": [{
                                    "ticker": "AAPL", 
                                    "action": "BUY", 
                                    "trade_id": 1, 
                                    "leg_id": 1, 
                                    "weight": 0.05
                                }, 
                                {
                                    "ticker": "MSFT", 
                                    "action": "SELL", 
                                    "trade_id": 1, 
                                    "leg_id": 2, 
                                    "weight": 0.05
                                }]
                            }]
        
        self.backtest_obj = Backtest(parameters = self.parameters,
                                 static_stats = self.static_stats,
                                 daily_timeseries_stats = self.timeseries_stats,
                                 period_timeseries_stats = self.timeseries_stats,
                                 trade_data = self.trades,
                                 signal_data = self.signals)
        
        response = self.client.create_backtest(self.backtest_obj)
        
        # Id for mocked backtest
        self.backtest_id = response['id'] 

        # Mock regression object
        self.regression_obj = RegressionResults(
            backtest= self.backtest_id,
            risk_free_rate=0.02,
            r_squared=0.95,
            adj_r_squared=0.94,
            RMSE=0.01,
            MAE=0.02,
            f_statistic=50.0,
            f_statistic_p_value=0.0001,
            durbin_watson=2.0,
            jarque_bera=5.0,
            jarque_bera_p_value=0.05,
            condition_number=10.0,
            vif={'beta1': 1.5, 'beta2': 2.0},
            alpha=0.05,
            p_value_alpha=0.01,
            beta={'beta1': 1.2, 'beta2': 0.8},
            p_value_beta={'beta1': 0.05, 'beta2': 0.01},
            total_contribution=0.5,
            systematic_contribution=0.3,
            idiosyncratic_contribution=0.2,
            total_volatility=0.15,
            systematic_volatility=0.1,
            idiosyncratic_volatility=0.05,
            timeseries_data=[
                {'timestamp': 1706850000000000000, 'daily_benchmark_return': 0.0}, 
                {'timestamp': 1707109200000000000, 'daily_benchmark_return': 0.0024}, 
                {'timestamp': 1707195600000000000, 'daily_benchmark_return': 0.0063}, 
                {'timestamp': 1707282000000000000, 'daily_benchmark_return': 0.0056}, 
                {'timestamp': 1707368400000000000, 'daily_benchmark_return': 0.0152}, 
                {'timestamp': 1707454800000000000, 'daily_benchmark_return': 0.0052}, 
                {'timestamp': 1707714000000000000, 'daily_benchmark_return': -0.0016}, 
                {'timestamp': 1707800400000000000, 'daily_benchmark_return': 0.0022}, 
                {'timestamp': 1707886800000000000, 'daily_benchmark_return': -0.0118}, 
                {'timestamp': 1707973200000000000, 'daily_benchmark_return': 0.0061}
            ]
        )
    
    def test_create_regression(self):
        # Test
        response = self.client.create_regression_analysis(self.regression_obj)

        # Validate
        self.assertIn('backtest', response)
        self.assertIn('r_squared', response) 
        self.assertIn('p_value_alpha', response) 
        self.assertIn('p_value_beta', response) 
        self.assertIn('risk_free_rate', response) 
        self.assertIn('alpha', response) 
        self.assertIn('beta', response) 
        
class TestBacktestMethods(unittest.TestCase):
    def setUp(self) -> None:
        # Database client
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 

        # Create mock backtest object
        self.parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": 1526601600000000000, 
                                "train_end": 1674086400000000000, 
                                "test_start": 1674086400000000000, 
                                "test_end": 1705622400000000000, 
                                "tickers": ["AAPL"], 
                                "benchmark": ["^GSPC"]
                            }
        self.static_stats = [{
                                "net_profit": 330.0, 
                                "total_fees": 40.0, 
                                "total_return": 0.33, 
                                "ending_equity": 1330.0, 
                                "max_drawdown": 0.0, 
                                "total_trades": 2, 
                                "num_winning_trades": 2, 
                                "num_lossing_trades": 0, 
                                "avg_win_percent": 0.45, 
                                "avg_loss_percent": 0, 
                                "percent_profitable": 1.0, 
                                "profit_and_loss": 0.0, 
                                "profit_factor": 0.0, 
                                "avg_trade_profit": 165.0, 
                                "sortino_ratio": 0.0
                            }]
        self.regression_stats=[{
                                "r_squared": "1.0", 
                                "p_value_alpha": "0.5", 
                                "p_value_beta": "0.09", 
                                "risk_free_rate": "0.01", 
                                "alpha": "16.4791", 
                                "beta": "-66.6633", 
                                "sharpe_ratio": "10.72015", 
                                "annualized_return": "39.0001", 
                                "market_contribution": "-0.498",
                                "idiosyncratic_contribution": "0.66319",
                                "total_contribution": "0.164998", 
                                "annualized_volatility": "3.7003", 
                                "market_volatility": "-0.25608",
                                "idiosyncratic_volatility": "7.85876", 
                                "total_volatility": "0.23608", 
                                "portfolio_dollar_beta": "-8862.27533", 
                                "market_hedge_nmv": "88662.2533"
                            }]
        self.timeseries_stats =  [
                                {
                                    "timestamp": 1702141200000000000,
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.330", 
                                    "daily_benchmark_return": "0.00499"
                                },
                                {
                                    "timestamp": 1702227600000000000,
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.087", 
                                    "daily_benchmark_return": "0.009"
                                }
                            ]
        self.trades =  [{
                                "trade_id": 1, 
                                "leg_id": 1, 
                                "timestamp": 1672704000000000000, 
                                "ticker": "AAPL", 
                                "quantity": 4, 
                                "avg_price": 130.74, 
                                "trade_value": -522.96, 
                                "action": "BUY", 
                                "fees": 0.0
                            }]
        self.signals =  [{
                                "timestamp": 1672704000000000000, 
                                "trade_instructions": [{
                                    "ticker": "AAPL", 
                                    "action": "BUY", 
                                    "trade_id": 1, 
                                    "leg_id": 1, 
                                    "weight": 0.05
                                }, 
                                {
                                    "ticker": "MSFT", 
                                    "action": "SELL", 
                                    "trade_id": 1, 
                                    "leg_id": 2, 
                                    "weight": 0.05
                                }]
                            }]
        
        self.backtest_obj = Backtest(parameters = self.parameters,
                                 static_stats = self.static_stats,
                                 daily_timeseries_stats = self.timeseries_stats,
                                 period_timeseries_stats = self.timeseries_stats,
                                 trade_data = self.trades,
                                 signal_data = self.signals)

    def test_create_backtest(self):
        # Test
        response = self.client.create_backtest(self.backtest_obj)

        # Validate
        self.assertIn("parameters", response)
        self.assertIn("static_stats", response)
        self.assertIn("regression_stats", response)
        self.assertIn("period_timeseries_stats", response)
        self.assertIn("daily_timeseries_stats", response)
        self.assertIn("signals", response)
        self.assertIn("trades", response)

    def test_get_backtest(self):
        # Test
        response=self.client.get_backtests()

        # Validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("id", response[0])
        self.assertIn("strategy_name", response[0])
        self.assertIn("tickers", response[0])
        self.assertIn("benchmark", response[0])
        self.assertIn("data_type", response[0])
        self.assertIn("train_start", response[0])
        self.assertIn("train_end", response[0])
        self.assertIn("test_start", response[0])
        self.assertIn("test_end", response[0])
        self.assertIn("capital", response[0])
    
    def test_get_backtest_by_id(self):
        # Create backtest to have its ID
        response = self.client.create_backtest(self.backtest_obj)
        id = response['id']

        # Test
        response=self.client.get_specific_backtest(backtest_id=id)

        # Validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("parameters", response)
        self.assertIn("static_stats", response)
        self.assertIn("regression_stats", response)
        self.assertIn("period_timeseries_stats", response)
        self.assertIn("daily_timeseries_stats", response)
        self.assertIn("signals", response)
        self.assertIn("trades", response)
        self.assertIn("price_data", response)

class TestTradingSessioMethods(unittest.TestCase):
    def setUp(self) -> None:
        # Database client
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 

        # Create test trading session object
        self.parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": 1526601600000000000, 
                                "train_end": 1674086400000000000, 
                                "test_start": 1674086400000000000, 
                                "test_end": 1705622400000000000,  
                                "tickers": ["HE", "ZC"], 
                                "benchmark": ["^GSPC"]
                            }
        self.acount = [{
                                "start_BuyingPower": "2557567.234", 
                                "currency": "USD", 
                                "start_ExcessLiquidity": "767270.345", 
                                "start_FullAvailableFunds": "767270.4837", 
                                "start_FullInitMarginReq": "282.3937", 
                                "start_FullMaintMarginReq": "282.3938", 
                                "start_FuturesPNL": "-464.883", 
                                "start_NetLiquidation": "767552.392", 
                                "start_TotalCashBalance": "-11292.332", 
                                "start_UnrealizedPnL": "0", 
                                "start_timestamp" :1712850009000000000, 
                                "end_BuyingPower": "2535588.9282", 
                                "end_ExcessLiquidity": "762034.2928", 
                                "end_FullAvailableFunds": "760676.292", 
                                "end_FullInitMarginReq": "7074.99", 
                                "end_FullMaintMarginReq": "5716.009", 
                                "end_FuturesPNL": "-487.998", 
                                "end_NetLiquidation": "767751.998", 
                                "end_TotalCashBalance": "766935.99", 
                                "end_UnrealizedPnL": "-28.99", 
                                "end_timestamp": 1712850137000000000
                            }]
        self.trades =  [
                                {"timestamp": 1712850060000000000, "ticker": "HE", "quantity": "1", "cumQty": "1", "price": "91.45", "AvPrice": "91.45", "action": "SELL", "cost": "0", "currency": "USD", "fees": "2.97"}, 
                                {"timestamp": 1712850060000000000, "ticker": "ZC", "quantity": "1", "cumQty": "1", "price": "446.25", "AvPrice": "446.25", "action": "BUY", "cost": "0", "currency": "USD", "fees": "2.97"}
                            ]
        self.signals =  [
                                {
                                    "timestamp": 1712850060000000000, 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }, 
                                {
                                    "timestamp": 1712850065000000000, 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }, 
                                {
                                    "timestamp": 1712850070000000000, 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }
                            ]

        self.session_obj = LiveTradingSession(parameters = self.parameters,
                                          account_data = self.acount,
                                          trade_data = self.trades,
                                          signal_data = self.signals)

    def test_create_live_session(self):
        # Test
        response =self.client.create_live_session(self.session_obj)

        # Validate
        self.assertIn("parameters", response)
        self.assertIn("account_data", response)
        self.assertIn("trades", response)
        self.assertIn("signals", response)

    def test_get_live_session(self):
        # Test
        response=self.client.get_live_sessions()

        # Validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("id", response[0])
        self.assertIn("strategy_name", response[0])
        self.assertIn("tickers", response[0])
        self.assertIn("benchmark", response[0])
        self.assertIn("data_type", response[0])
        self.assertIn("train_start", response[0])
        self.assertIn("train_end", response[0])
        self.assertIn("test_start", response[0])
        self.assertIn("test_end", response[0])
        self.assertIn("capital", response[0])
    
    def test_get_specific_session(self):
        # Create  session for ID
        response =self.client.create_live_session(self.session_obj)
        id = response['id']

        # Test
        response=self.client.get_specific_live_session(live_session_id=id)

        # Validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("parameters", response)
        self.assertIn("account_data", response)
        self.assertIn("trades", response)
        self.assertIn("signals", response)
        self.assertIn("price_data", response)

class TestPortfolioDataMethods(unittest.TestCase):
    def setUp(self) -> None:
        # Database client
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL)     

        # Create Session
        self.session_id = 12345
        self.client.create_session(self.session_id)
    
    def test_create_session(self):
        session_id = 12346

        # Test
        response = self.client.create_session(session_id)

        # Validation
        self.assertEqual(response, { "session_id": session_id })

        # Clean-up
        self.client.delete_session(session_id)

    def test_delete_session(self):
        session_id = 12346

        # Create session to be deleted
        self.client.create_session(session_id)
        
        # Test
        response = self.client.delete_session(session_id)

        # Validate
        self.assertEqual(response["status_code"], 204)

    def test_create_position(self):
        position = {
                "data": {
                    "action" : "BUY",
                    "avg_cost" : 150,
                    "quantity" : 100,
                    "total_cost" : 15000.00,
                    "market_value" : 160000.11,
                    "multiplier" : 1, 
                    "initial_margin" : 0.0,
                    "ticker" : "AAPL",
                    "price" : 160
                    }       
                }


        # Test
        response = self.client.create_positions(self.session_id, position)

        # Validation
        expected_data = position["data"] 
        self.assertEqual(response['data'], expected_data)

    def test_update_position(self):
        # Create position
        position = {
                "data": {
                    "action" : "BUY",
                    "avg_cost" : 150,
                    "quantity" : 100,
                    "total_cost" : 15000.00,
                    "market_value" : 160000.11,
                    "multiplier" : 1, 
                    "initial_margin" : 0.0,
                    "ticker" : "AAPL",
                    "price" : 160
                    }       
                }
        self.client.create_positions(self.session_id, position)

        # Test
        position['data']['action'] = "SELL"
        response = self.client.update_positions(self.session_id, position)

        # Validation
        expected_data = position["data"]
        self.assertEqual(response['data'], expected_data)

    def test_get_position(self):
        # Create position
        data = {
                "data": {
                    "action" : "BUY",
                    "avg_cost" : 150,
                    "quantity" : 100,
                    "total_cost" : 15000.00,
                    "market_value" : 160000.11,
                    "multiplier" : 1, 
                    "initial_margin" : 0.0,
                    "ticker" : "AAPL",
                    "price" : 160
                    }       
                }
        self.client.create_positions(self.session_id, data)

        # Test
        response = self.client.get_positions(self.session_id)

        # Validation
        self.assertEqual(response['data'], data['data'])

    def test_create_order(self):
        data = {
                "data" : {
                    "permId" : 1,
                    "clientId" : 22,
                    "orderId" : 5,
                    "parentId" : 5,
                    "account": "DU12546",
                    "symbol" : "AAPL",
                    "secType" : "STK",
                    "exchange": "NASDAQ",
                    "action" : "BUY",
                    "orderType" : "MKT",
                    "totalQty" : 1009.90,
                    "cashQty" : 109.99,
                    "lmtPrice" : 0.0,
                    "auxPrice" : 0.0,
                    "status" : "Submitted",
                    "filled" : "9",
                    "remaining" : 10,
                    "avgFillPrice" : 100, 
                    "lastFillPrice": 100,
                    "whyHeld" : "",
                    "mktCapPrice" : 1000.99
                }
            }
        
        # Test
        response = self.client.create_orders(self.session_id, data)

        # Validation
        self.assertEqual(response['data'], data['data'])

    def test_update_order(self):
        # Create order
        data = {
                "data" : {
                    "permId" : 1,
                    "clientId" : 22,
                    "orderId" : 5,
                    "parentId" : 5,
                    "account": "DU12546",
                    "symbol" : "AAPL",
                    "secType" : "STK",
                    "exchange": "NASDAQ",
                    "action" : "BUY",
                    "orderType" : "MKT",
                    "totalQty" : 1009.90,
                    "cashQty" : 109.99,
                    "lmtPrice" : 0.0,
                    "auxPrice" : 0.0,
                    "status" : "Submitted",
                    "filled" : "9",
                    "remaining" : 10,
                    "avgFillPrice" : 100, 
                    "lastFillPrice": 100,
                    "whyHeld" : "",
                    "mktCapPrice" : 1000.99
                }
            }
        
        self.client.create_orders(self.session_id, data)

        # Test
        data['data']['permId'] = 100
        response = self.client.update_orders(self.session_id, data)

        # Validation
        self.assertEqual(response['data'], data['data'])

    def test_get_order(self):
        # Create order
        data = {
                "data" : {
                    "permId" : 1,
                    "clientId" : 22,
                    "orderId" : 5,
                    "parentId" : 5,
                    "account": "DU12546",
                    "symbol" : "AAPL",
                    "secType" : "STK",
                    "exchange": "NASDAQ",
                    "action" : "BUY",
                    "orderType" : "MKT",
                    "totalQty" : 1009.90,
                    "cashQty" : 109.99,
                    "lmtPrice" : 0.0,
                    "auxPrice" : 0.0,
                    "status" : "Submitted",
                    "filled" : "9",
                    "remaining" : 10,
                    "avgFillPrice" : 100, 
                    "lastFillPrice": 100,
                    "whyHeld" : "",
                    "mktCapPrice" : 1000.99
                }
            }
        
        self.client.create_orders(self.session_id, data)

        # Test
        response = self.client.get_orders(self.session_id)

        # Validation
        self.assertEqual(response['data'], data['data'])

    def test_create_account(self):
        data = {
                "data" : {
                    "Timestamp" : "2024-01-01",
                    "FullAvailableFunds" : 1000.99,
                    "FullInitMarginReq" : 99980.99,
                    "NetLiquidation" : 99.98,
                    "UnrealizedPnL" : 1000.9,
                    "FullMaintMarginReq" : 86464.39,
                    "ExcessLiquidity" : 99333.99,
                    "Currency" : "USD",
                    "BuyingPower" : 777.89,
                    "FuturesPNL" : 564837.99,
                    "TotalCashBalance" : 999.99
                }
            }
        
        # Test
        response = self.client.create_account(self.session_id, data)

        # Validation
        self.assertEqual(response['data'], data['data'])

    def test_update_account(self):
        # Create account
        data = {
                "data" : {
                    "Timestamp" : "2024-01-01",
                    "FullAvailableFunds" : 1000.99,
                    "FullInitMarginReq" : 99980.99,
                    "NetLiquidation" : 99.98,
                    "UnrealizedPnL" : 1000.9,
                    "FullMaintMarginReq" : 86464.39,
                    "ExcessLiquidity" : 99333.99,
                    "Currency" : "USD",
                    "BuyingPower" : 777.89,
                    "FuturesPNL" : 564837.99,
                    "TotalCashBalance" : 999.99
                }
            }
        
        self.client.create_account(self.session_id, data)

        # Test
        data['data']['FullAvailableFunds'] = 1111.99
        response = self.client.update_account(self.session_id, data)

        # Validation
        self.assertEqual(response['data'], data['data'])

    def test_get_account(self):
        # Create account
        data = {
                "data" : {
                    "Timestamp" : "2024-01-01",
                    "FullAvailableFunds" : 1000.99,
                    "FullInitMarginReq" : 99980.99,
                    "NetLiquidation" : 99.98,
                    "UnrealizedPnL" : 1000.9,
                    "FullMaintMarginReq" : 86464.39,
                    "ExcessLiquidity" : 99333.99,
                    "Currency" : "USD",
                    "BuyingPower" : 777.89,
                    "FuturesPNL" : 564837.99,
                    "TotalCashBalance" : 999.99
                }
            }
        
        self.client.create_account(self.session_id, data)

        # Test
        response = self.client.get_account(self.session_id)

        # Validation
        self.assertEqual(response['data'], data['data'])
       
    def tearDown(self) -> None:
        # Delete Session
        self.client.delete_session(self.session_id) 

if __name__ == "__main__":
    unittest.main()

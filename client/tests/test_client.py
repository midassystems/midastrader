import unittest
import copy
from decouple import config

from client.client import DatabaseClient
from shared.data import *

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

# !!!!!! Best if working with a blank dev database for testing  !!!!!!!!!!!!
# run twice and only error shoudl be already exitsin the symbol data

# class TestSymbolDataMethods(unittest.TestCase):
#     def setUp(self) -> None:
#         self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 

#     # -- Symbol Data -- 
#     def test_create_asset_class(self):
#         asset_class = AssetClass.EQUITY
        
#         # Test
#         response = self.client.create_asset_class(asset_class)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertEqual(response["value"],asset_class.value)

#     def test_create_asset_class_invalid(self):
#         with self.assertRaises(TypeError):
#             self.client.create_asset_class("asset_class")

#     def test_get_asset_class(self):
#         asset_class = AssetClass.CRYPTOCURRENCY
#         self.client.create_asset_class(asset_class)
        
#         # Test
#         response = self.client.get_asset_classes()

#         # Validate
#         self.assertTrue(len(response) > 0)

#     def test_update_asset_class(self):
#         asset_class = AssetClass.COMMODITY
#         old_response = self.client.create_asset_class(asset_class)
        
#         # Test
#         response = self.client.update_asset_class(old_response["id"], AssetClass.FOREX)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertTrue(response["value"], "FOREX")
#         self.assertTrue(response["id"], old_response["id"])

#     def test_create_security_type(self):
#         security_type = SecurityType.FUTURE
        
#         # Test
#         response = self.client.create_security_type(security_type)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertEqual(response["value"],security_type.value)

#     def test_create_security_type_invalid(self):
#         with self.assertRaises(TypeError):
#             self.client.create_security_type("security_type")

#     def test_get_security_type(self):
#         security_type = SecurityType.STOCK
#         self.client.create_security_type(security_type)
        
#         # Test
#         response = self.client.get_security_types()

#         # Validate
#         self.assertTrue(len(response) > 0)

#     def test_update_security_type(self):
#         security_type = SecurityType.OPTION
#         old_response = self.client.create_security_type(security_type)
        
#         # Test
#         new_security_type = SecurityType.INDEX
#         response = self.client.update_security_type(old_response["id"], new_security_type)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertTrue(response["value"], new_security_type.value)
#         self.assertTrue(response["id"], old_response["id"])

#     def test_create_venue(self):
#         venue = Venue.CME
        
#         # Test
#         response = self.client.create_venue(venue)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertEqual(response["value"],venue.value)

#     def test_create_venue_invalid(self):
#         with self.assertRaises(TypeError):
#             self.client.create_venue("venue")

#     def test_get_venue(self):
#         venue = Venue.NASDAQ
#         self.client.create_venue(venue)
        
#         # Test
#         response = self.client.get_venues()

#         # Validate
#         self.assertTrue(len(response) > 0)

#     def test_update_venue(self):
#         venue = Venue.CBOT
#         old_response = self.client.create_venue(venue)
        
#         # Test
#         new_venue = Venue.NYSE
#         response = self.client.update_venue(old_response["id"], new_venue)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertTrue(response["value"], new_venue.value)
#         self.assertTrue(response["id"], old_response["id"])

#     def test_create_currency(self):
#         currency = Currency.USD
        
#         # Test
#         response = self.client.create_currency(currency)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertEqual(response["value"],currency.value)

#     def test_create_currency_invalid(self):
#         with self.assertRaises(TypeError):
#             self.client.create_currency("currency")

#     def test_get_currency(self):
#         currency = Currency.AUD
#         self.client.create_currency(currency)
        
#         # Test
#         response = self.client.get_currencies()

#         # Validate
#         self.assertTrue(len(response) > 0)

#     def test_update_currency(self):
#         currency = Currency.JPY
#         old_response = self.client.create_currency(currency)
        
#         # Test
#         new_currency = Currency.GBP
#         response = self.client.update_currency(old_response["id"], new_currency)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertTrue(response["value"], new_currency.value)
#         self.assertTrue(response["id"], old_response["id"])

#     def test_create_industry(self):
#         industry = Industry.TECHNOLOGY
        
#         # Test
#         response = self.client.create_industry(industry)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertEqual(response["value"],industry.value)

#     def test_create_industry_invalid(self):
#         with self.assertRaises(TypeError):
#             self.client.create_industry("industry")

#     def test_get_industry(self):
#         industry = Industry.AGRICULTURE
#         self.client.create_industry(industry)
        
#         # Test
#         response = self.client.get_industries()

#         # Validate
#         self.assertTrue(len(response) > 0)

#     def test_update_industry(self):
#         industry = Industry.COMMUNICATION
#         old_response = self.client.create_industry(industry)
        
#         # Test
#         new_industry = Industry.MATERIALS
#         response = self.client.update_industry(old_response["id"], new_industry)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertTrue(response["value"], new_industry.value)
#         self.assertTrue(response["id"], old_response["id"])

#     def test_create_contract_units(self):
#         contract_units = ContractUnits.BARRELS
        
#         # Test
#         response = self.client.create_contract_units(contract_units)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertEqual(response["value"],contract_units.value)

#     def test_create_contract_units_invalid(self):
#         with self.assertRaises(TypeError):
#             self.client.create_contract_units("contract_units")

#     def test_get_contract_units(self):
#         contract_units = ContractUnits.BUSHELS
#         self.client.create_contract_units(contract_units)
        
#         # Test
#         response = self.client.get_contract_units()

#         # Validate
#         self.assertTrue(len(response) > 0)

#     def test_update_contract_units(self):
#         contract_units = ContractUnits.METRIC_TON
#         old_response = self.client.create_contract_units(contract_units)
        
#         # Test
#         new_contract_units = ContractUnits.POUNDS
#         response = self.client.update_contract_units(old_response["id"], new_contract_units)

#         # Validate
#         self.assertTrue(len(response) > 0)
#         self.assertTrue(response["value"], new_contract_units.value)
#         self.assertTrue(response["id"], old_response["id"])

class TestSymbolMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 


    def setUp(self) -> None:
        self.equity = Equity(ticker="AAPL",
                                security_type=SecurityType.STOCK,
                                company_name="Apple Inc.",
                                venue=Venue.NASDAQ,
                                currency=Currency.USD,
                                industry=Industry.TECHNOLOGY,
                                market_cap=10000000000.99,
                                shares_outstanding=1937476363)

        self.future=Future(ticker = "HEJ4",
                            security_type = SecurityType.FUTURE,
                            product_code="HE",
                            product_name="Lean Hogs",
                            venue=Venue.CME,
                            currency=Currency.USD,
                            industry=Industry.AGRICULTURE,
                            contract_size=40000,
                            contract_units=ContractUnits.POUNDS,
                            tick_size=0.00025,
                            min_price_fluctuation=10,
                            continuous=False)

        self.option=Option(ticker = "AAPLP",
                            security_type = SecurityType.OPTION, 
                            strike_price=109.99,
                            currency=Currency.USD,
                            venue=Venue.NASDAQ,
                            expiration_date="2024-01-01",
                            option_type="CALL",
                            contract_size=100,
                            underlying_name="AAPL Inc")

        self.index=Index(ticker="GSPC",
                            security_type=SecurityType.INDEX,
                            name="S&P 500",
                            currency=Currency.USD,
                            asset_class=AssetClass.EQUITY,
                            venue= Venue.NASDAQ)
        
    def test_create_symbol_equity(self):
        # test 
        response = self.client.create_symbol(self.equity)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.equity.ticker)

        self.client.delete_symbol(response["id"])

    def test_create_symbol_future(self):
        # test 
        response = self.client.create_symbol(self.future)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.future.ticker)

        self.client.delete_symbol(response["id"])

    def test_create_symbol_option(self):
        # test 
        response = self.client.create_symbol(self.option)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.option.ticker)

        self.client.delete_symbol(response["id"])

    def test_create_symbol_index(self):
        # test 
        response = self.client.create_symbol(self.index)

        # validate
        self.assertTrue(len(response) > 1)
        self.assertEqual(response["ticker"], self.index.ticker)

        self.client.delete_symbol(response["id"])

    def test_update_symbol(self):
        equity = self.equity
        equity.ticker = "Test8"
        old_response=self.client.create_symbol(equity)

        # test
        equity.ticker = "Test9"
        response=self.client.update_symbol(symbol_id=old_response["id"], symbol=equity)

        # validate
        self.assertEqual(old_response["id"], response["id"])
        self.assertEqual(response["ticker"], equity.ticker)

        # clean up
        self.client.delete_symbol(response["id"])

    def test_delete_symbol(self):  
        symbol = self.client.create_symbol(self.equity) 

        # test 
        self.client.delete_symbol(symbol["id"])

        # validate
        response=self.client.get_symbols()
        for i in response:
            self.assertTrue(i["ticker"] != "AAPL")

    def test_get_symbol_by_ticker(self):
        ticker="HEJ4"
        symbol=self.client.create_symbol(self.future)
        
        # test
        response=self.client.get_symbol_by_ticker(ticker)[0]

        # Validate
        self.assertEqual(response["ticker"], ticker)
        self.assertEqual(response["security_type"], "FUTURE")
        
        # clean up
        self.client.delete_symbol(symbol["id"])

    def test_get_symbols_list(self):
        response_eq=self.client.create_symbol(self.equity)
        response_fu = self.client.create_symbol(self.future)

        # test
        response=self.client.get_symbols()

        # validate
        tickers=[]
        for i in response:
            tickers.append(i['ticker'])

        self.assertGreaterEqual(len(response), 1)
        self.assertIn(self.future.ticker,tickers)
        self.assertIn(self.equity.ticker,tickers)

        # clean up
        self.client.delete_symbol(response_fu["id"])
        self.client.delete_symbol(response_eq["id"])
            
    def test_get_equity_list(self):
        symbol=self.client.create_symbol(self.equity)

        # test
        response=self.client.get_equity()
        
        # validate
        self.assertGreaterEqual(len(response), 1)

        # clean-up
        self.client.delete_symbol(symbol["id"])

    def test_get_future_list(self):
        symbol=self.client.create_symbol(self.future)

        # test
        response=self.client.get_future()
        
        # validate
        self.assertGreaterEqual(len(response), 1)

        # clean up
        self.client.delete_symbol(symbol["id"])

    def test_get_indexes_list(self):
        symbol = self.client.create_symbol(self.index)

        # test
        response=self.client.get_indexes()
        
        # validate
        self.assertGreaterEqual(len(response), 1)

        # clean-up
        self.client.delete_symbol(symbol["id"])

    # def test_get_options_list(self):
    #     # test
    #     response=self.client.get_options()
        
    #     # validate
    #     self.assertGreaterEqual(len(response), 1)

class TestMarketDataMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 
        cls.ticker="AAPL4"

        cls.equity = Equity(ticker="AAPL4",
                                security_type=SecurityType.STOCK,
                                company_name="Apple Inc.",
                                venue=Venue.NASDAQ,
                                currency=Currency.USD,
                                industry=Industry.TECHNOLOGY,
                                market_cap=10000000000.99,
                                shares_outstanding=1937476363)
        cls.symbol=cls.client.create_symbol(cls.equity)
    
    def setUp(self) -> None:
        self.bar=BarData(ticker="AAPL4",
                            timestamp=np.uint64(1711100000),
                            open=Decimal('99.9999'),
                            high=Decimal('100.9999'),
                            low=Decimal('100.9999'),
                            close=Decimal('100.9999'),
                            volume=np.uint64(100),
                            )
        
        self.bar2 = copy.deepcopy(self.bar)
        self.bar2.timestamp = np.uint64(1711200000)

        self.bar3 = copy.deepcopy(self.bar)
        self.bar3.timestamp = np.uint64(1711300000)

        self.bars = [self.bar2,self.bar3]

        
        # self.quote=QuoteData(ticker="AAPL3",
        #                         timestamp="2024-01-10",
        #                         ask=90.999,
        #                         ask_size=9849.999,
        #                         bid=89.99,
        #                         bid_size=9990.8778
        #                     ) 

    def test_get_bar_data_ticker_and_dates(self):
        tickers=[self.ticker]
        start_date="2020-01-01"
        end_date="2025-01-01"
        
        # test
        response=self.client.get_bar_data(tickers, start_date, end_date)

        # valdiate
        self.assertGreaterEqual(len(response), 1)

    def test_create_bar_data(self):
        # test
        response=self.client.create_bar_data(self.bar)

        # valdiate
        self.assertIn( "id", response)
        self.assertEqual(response['symbol'], self.bar.ticker)
        self.assertEqual(response['timestamp'], self.bar.timestamp)
        self.assertEqual(Decimal(response['open']), self.bar.open)
        self.assertEqual(Decimal(response['high']), self.bar.high)
        self.assertEqual(Decimal(response['low']), self.bar.low)
        self.assertEqual(Decimal(response['close']), self.bar.close)
        self.assertEqual(response['volume'], self.bar.volume)

    def test_create_bulk_bar_data(self):
        # test
        response=self.client.create_bulk_price_data(self.bars)

        # validate
        self.assertEqual(len(response['batch_responses'][0]['created']), 2)
        self.assertEqual(len(response['batch_responses'][0]['errors']), 0)

    def test_create_bulk_bar_data_with_overlap(self):
        bar4 = copy.deepcopy(self.bar)
        bar4.timestamp = 1707221190000000000

        self.bars.append(bar4)
        
        # test
        response= self.client.create_bulk_price_data(self.bars)

        # validate
        self.assertEqual(len(response['batch_responses'][0]['created']), 1)
        self.assertEqual(len(response['batch_responses'][0]['errors']), 2)

    def test_update_data(self):

        bar=BarData(ticker="AAPL4",
                    timestamp=np.uint64(1712200000),
                    open=Decimal('99.9999'),
                    high=Decimal('100.9999'),
                    low=Decimal('100.9999'),
                    close=Decimal('100.9999'),
                    volume=np.uint64(100),
                    )
        self.client.create_bar_data(bar)

        tickers=[self.ticker]
        start_date="2024-03-01"
        end_date="2024-05-01"
        old_bar=self.client.get_bar_data(tickers, start_date, end_date)[0]

        new_bar = copy.deepcopy(self.bar)
        new_bar.open = Decimal("0.0009")

        # test
        response=self.client.update_bar_data(old_bar['id'], new_bar)

        # validate
        self.assertEqual(old_bar['id'], response['id'])
        self.assertEqual(Decimal(response['open']), new_bar.open)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.delete_symbol(cls.symbol["id"])

class TestBacktestMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 
        self.mock_parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": "2018-05-18", 
                                "train_end": "2023-01-19", 
                                "test_start": "2023-01-19", 
                                "test_end": "2024-01-19", 
                                "tickers": ["AAPL"], 
                                "benchmark": ["^GSPC"]
                            }
        self.mock_static_stats = [{
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
        self.mock_regression_stats=[{
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
        self.mock_timeseries_stats =  [
                                {
                                    "timestamp": "2023-12-09T12:00:00Z",
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.330", 
                                    "daily_benchmark_return": "0.00499"
                                },
                                {
                                    "timestamp": "2023-12-10T12:00:00Z",
                                    "equity_value": 10000.0,
                                    "percent_drawdown": 9.9, 
                                    "cumulative_return": -0.09, 
                                    "period_return": 79.9,
                                    "daily_strategy_return": "0.087", 
                                    "daily_benchmark_return": "0.009"
                                }
                            ]
        self.mock_trades =  [{
                                "trade_id": 1, 
                                "leg_id": 1, 
                                "timestamp": "2023-01-03T00:00:00+0000", 
                                "ticker": "AAPL", 
                                "quantity": 4, 
                                "price": 130.74, 
                                "cost": -522.96, 
                                "action": "BUY", 
                                "fees": 0.0
                            }]
        self.mock_signals =  [{
                                "timestamp": "2023-01-03T00:00:00+0000", 
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
        
        self.backtest = Backtest(parameters = self.mock_parameters,
                                 static_stats = self.mock_static_stats,
                                 regression_stats=self.mock_regression_stats,
                                 timeseries_stats = self.mock_timeseries_stats,
                                 trade_data = self.mock_trades,
                                 signal_data = self.mock_signals)

    def test_create_backtest(self):
        # test
        response =self.client.create_backtest(self.backtest)

        # validate
        self.assertIn("parameters", response)
        self.assertIn("static_stats", response)
        self.assertIn("regression_stats", response)
        self.assertIn("timeseries_stats", response)
        self.assertIn("signals", response)
        self.assertIn("trades", response)

    def test_get_backtest(self):
        # test
        response=self.client.get_backtests()

        # validate
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
        response =self.client.create_backtest(self.backtest)

        # test
        response=self.client.get_specific_backtest(response['id'])

        # validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("parameters", response)
        self.assertIn("static_stats", response)
        self.assertIn("regression_stats", response)
        self.assertIn("timeseries_stats", response)
        self.assertIn("signals", response)
        self.assertIn("trades", response)
        self.assertIn("price_data", response)

class TestTradingSessioMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL) 
        self.mock_parameters = {
                                "strategy_name": "cointegrationzscore", 
                                "capital": 100000, 
                                "data_type": "BAR", 
                                "train_start": "2020-05-18", 
                                "train_end": "2024-01-01", 
                                "test_start": "2024-01-02", 
                                "test_end": "2024-01-19", 
                                "tickers": ["HE", "ZC"], 
                                "benchmark": ["^GSPC"]
                            }
        self.mock_acount = [{
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
                                "start_timestamp": "2024-04-11T11:40:09.861731", 
                                "end_BuyingPower": "2535588.9282", 
                                "end_ExcessLiquidity": "762034.2928", 
                                "end_FullAvailableFunds": "760676.292", 
                                "end_FullInitMarginReq": "7074.99", 
                                "end_FullMaintMarginReq": "5716.009", 
                                "end_FuturesPNL": "-487.998", 
                                "end_NetLiquidation": "767751.998", 
                                "end_TotalCashBalance": "766935.99", 
                                "end_UnrealizedPnL": "-28.99", 
                                "end_timestamp": "2024-04-11T11:42:17.046984"
                            }]
        self.mock_trades =  [
                                {"timestamp": "2024-04-11T15:41:00+00:00", "ticker": "HE", "quantity": "1", "cumQty": "1", "price": "91.45", "AvPrice": "91.45", "action": "SELL", "cost": "0", "currency": "USD", "fees": "2.97"}, 
                                {"timestamp": "2024-04-11T15:41:00+00:00", "ticker": "ZC", "quantity": "1", "cumQty": "1", "price": "446.25", "AvPrice": "446.25", "action": "BUY", "cost": "0", "currency": "USD", "fees": "2.97"}
                            ]
        self.mock_signals =  [
                                {
                                    "timestamp": "2024-04-11T15:41:00+00:00", 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }, 
                                {
                                    "timestamp": "2024-04-11T15:41:05+00:00", 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }, 
                                {
                                    "timestamp": "2024-04-11T15:41:10+00:00", 
                                    "trade_instructions": [
                                        {"ticker": "HE", "order_type": "MKT", "action": "SHORT", "trade_id": 1, "leg_id": 1, "weight": "-0.8689"}, 
                                        {"ticker": "ZC", "order_type": "MKT", "action": "LONG", "trade_id": 1, "leg_id": 2, "weight": "0.1311"}
                                    ]
                                }
                            ]

        self.session = LiveTradingSession(parameters = self.mock_parameters,
                                          account_data = self.mock_acount,
                                          trade_data = self.mock_trades,
                                          signal_data = self.mock_signals)

    def test_create_live_session(self):
        # test
        response =self.client.create_live_session(self.session)

        # validate
        self.assertIn("parameters", response)
        self.assertIn("account_data", response)
        self.assertIn("trades", response)
        self.assertIn("signals", response)

    def test_get_live_session(self):
        # test
        response=self.client.get_live_sessions()

        # validate
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
        response =self.client.create_live_session(self.session)

        # test
        response=self.client.get_specific_live_session(response['id'])

        # validate
        self.assertGreaterEqual(len(response), 1)
        self.assertIn("parameters", response)
        self.assertIn("account_data", response)
        self.assertIn("trades", response)
        self.assertIn("signals", response)
        self.assertIn("price_data", response)

class TestPortfolioDataMethods(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DatabaseClient(DATABASE_KEY, DATABASE_URL)     
    
    def test_create_session(self):
        session_id = 12345

        # test
        response = self.client.create_session(session_id)

        # validation
        self.assertEqual(response, { "session_id": session_id })

        # clean up
        self.client.delete_session(session_id)

    def test_delete_session(self):
        session_id = 12345
        self.client.create_session(session_id)
        
        # test
        self.client.delete_session(session_id)

    def test_create_position(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        # test
        response = self.client.create_positions(session_id, data)

        # validation
        expected_data = {'action': 'BUY', 'avg_cost': 150, 'quantity': 100, 'total_cost': 15000.0, 'market_value': 160000.11, 'multiplier': 1, 'initial_margin': 0.0, 'ticker': 'AAPL', 'price': 160}
        self.assertEqual(response['data'], expected_data)

        # clean up
        self.client.delete_session(session_id)

    def test_update_position(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        self.client.create_positions(session_id, data)

        # test
        data['data']['action'] = "SELL"
        response = self.client.update_positions(session_id, data)

        # validation
        expected_data = {'action': 'SELL', 'avg_cost': 150, 'quantity': 100, 'total_cost': 15000.0, 'market_value': 160000.11, 'multiplier': 1, 'initial_margin': 0.0, 'ticker': 'AAPL', 'price': 160}
        self.assertEqual(response['data'], expected_data)

        # clean up
        self.client.delete_session(session_id)

    def test_get_position(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        self.client.create_positions(session_id, data)

        # test
        response = self.client.get_positions(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_create_order(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        
        # test
        response = self.client.create_orders(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_update_order(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        
        self.client.create_orders(session_id, data)

        # test
        data['data']['permId'] = 100
        response = self.client.update_orders(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_get_order(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        
        self.client.create_orders(session_id, data)

        # test
        response = self.client.get_orders(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_create_account(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        
        # test
        response = self.client.create_account(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_update_account(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        
        self.client.create_account(session_id, data)

        # test
        data['data']['FullAvailableFunds'] = 1111.99
        response = self.client.update_account(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)

    def test_get_account(self):
        session_id = 12345
        self.client.create_session(session_id)
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
        
        self.client.create_account(session_id, data)

        # test
        response = self.client.get_account(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.client.delete_session(session_id)
        

if __name__ == "__main__":
    unittest.main()

import unittest
from decouple import config

from midas_database.client import DatabaseClient

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')


class TestDatabaseClient(unittest.TestCase):
    def setUp(self) -> None:
        self.database_client = DatabaseClient(DATABASE_KEY,DATABASE_URL) 

    # Basic Validation
    def test_create_session(self):
        session_id = 12345

        # test
        response = self.database_client.create_session(session_id)

        # validation
        self.assertEqual(response, { "session_id": session_id })

        # clean up
        self.database_client.delete_session(session_id)

    def test_delete_session(self):
        session_id = 12345
        self.database_client.create_session(session_id)
        
        # test
        self.database_client.delete_session(session_id)

    def test_create_position(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        response = self.database_client.create_positions(session_id, data)

        # validation
        expected_data = {'action': 'BUY', 'avg_cost': 150, 'quantity': 100, 'total_cost': 15000.0, 'market_value': 160000.11, 'multiplier': 1, 'initial_margin': 0.0, 'ticker': 'AAPL', 'price': 160}
        self.assertEqual(response['data'], expected_data)

        # clean up
        self.database_client.delete_session(session_id)

    def test_update_position(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        self.database_client.create_positions(session_id, data)

        # test
        data['data']['action'] = "SELL"
        response = self.database_client.update_positions(session_id, data)

        # validation
        expected_data = {'action': 'SELL', 'avg_cost': 150, 'quantity': 100, 'total_cost': 15000.0, 'market_value': 160000.11, 'multiplier': 1, 'initial_margin': 0.0, 'ticker': 'AAPL', 'price': 160}
        self.assertEqual(response['data'], expected_data)

        # clean up
        self.database_client.delete_session(session_id)

    def test_get_position(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        self.database_client.create_positions(session_id, data)

        # test
        response = self.database_client.get_positions(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.database_client.delete_session(session_id)

    def test_create_order(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        response = self.database_client.create_orders(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.database_client.delete_session(session_id)

    def test_update_order(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        
        self.database_client.create_orders(session_id, data)

        # test
        data['data']['permId'] = 100
        response = self.database_client.update_orders(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.database_client.delete_session(session_id)

    def test_get_order(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        
        self.database_client.create_orders(session_id, data)

        # test
        response = self.database_client.get_orders(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.database_client.delete_session(session_id)

    def test_create_account(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        response = self.database_client.create_account(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.database_client.delete_session(session_id)

    def test_update_account(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        
        self.database_client.create_account(session_id, data)

        # test
        data['data']['FullAvailableFunds'] = 1111.99
        response = self.database_client.update_account(session_id, data)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.database_client.delete_session(session_id)

    def test_get_account(self):
        session_id = 12345
        self.database_client.create_session(session_id)
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
        
        self.database_client.create_account(session_id, data)

        # test
        response = self.database_client.get_account(session_id)

        # validation
        self.assertEqual(response['data'], data['data'])

        # clean up
        self.database_client.delete_session(session_id)
        

    # def test_create_live_session(self):
    #     data = {
    #                 "parameters": {
    #                     "strategy_name": "cointegrationzscore", 
    #                     "capital": 100000, 
    #                     "data_type": "BAR", 
    #                     "train_start": "2018-05-18", 
    #                     "train_end": "2023-01-19", 
    #                     "test_start": "2023-01-19", 
    #                     "test_end": "2024-01-19", 
    #                     "tickers": ["HE.n.0", "ZC.n.0"], 
    #                     "benchmark": ["^GSPC"]
    #                 },
    #                 "static_stats": [{
    #                     'net_profit': None, 
    #                     'total_return': 10.0, 
    #                     'max_drawdown': None, 
    #                     'annual_standard_deviation': None, 
    #                     'ending_equity': None, 
    #                     'total_fees': 2.5, 
    #                     'total_trades': 5, 
    #                     'num_winning_trades': None, 
    #                     'num_lossing_trades': None, 
    #                     'avg_win_percent': None, 
    #                     'avg_loss_percent': None, 
    #                     'percent_profitable': None, 
    #                     'profit_and_loss': None,
    #                     'profit_factor': None, 
    #                     'avg_trade_profit': None, 
    #                     'sharpe_ratio': None, 
    #                     'sortino_ratio': None, 
    #                     'alpha': None, 
    #                     'beta': None
    #                 }],
    #                 "timeseries_stats": [
    #                     {
    #                         "timestamp": "2023-12-09T12:00:00Z",
    #                         "equity_value": 10000.0,
    #                         "percent_drawdown": 9.9, 
    #                         "cumulative_return": -0.09, 
    #                         "daily_return": 79.9
    #                     },
    #                     {
    #                         "timestamp": "2023-12-10T12:00:00Z",
    #                         "equity_value": 10000.0,
    #                         "percent_drawdown": 9.9, 
    #                         "cumulative_return": -0.09, 
    #                         "daily_return": 79.9
    #                     }
    #                 ],
    #                 "trades": [{
    #                     "trade_id": 1, 
    #                     "leg_id": 1, 
    #                     "timestamp": "2023-01-03T00:00:00+0000", 
    #                     "ticker": "AAPL", 
    #                     "quantity": 4, 
    #                     "price": 130.74, 
    #                     "cost": -522.96, 
    #                     "action": "BUY", 
    #                     "fees": 0.0
    #                 }],
    #                 "signals": [{
    #                     "timestamp": "2023-01-03T00:00:00+0000", 
    #                     "trade_instructions": [{
    #                         "ticker": "AAPL", 
    #                         "action": "BUY", 
    #                         "trade_id": 1, 
    #                         "leg_id": 1, 
    #                         "weight": 0.05
    #                     }, 
    #                     {
    #                         "ticker": "MSFT", 
    #                         "action": "SELL", 
    #                         "trade_id": 1, 
    #                         "leg_id": 2, 
    #                         "weight": 0.05
    #                     }]
    #                 }]
    #             }

    #     # Test
    #     response = self.database_client.create_live_session(data)
    #     actual = self.database_client.get_specific_live_session(response['id'])

    #     # Validate
    #     self.assertNotEqual(response, {})
    #     self.assertNotEqual(actual, None)

    # def test_get_lives_sessions(self):
    #     data = {
    #         "parameters": {
    #             "strategy_name": "cointegrationzscore", 
    #             "capital": 100000, 
    #             "data_type": "BAR", 
    #             "train_start": "2018-05-18", 
    #             "train_end": "2023-01-19", 
    #             "test_start": "2023-01-19", 
    #             "test_end": "2024-01-19", 
    #             "tickers": ["HE.n.0", "ZC.n.0"], 
    #             "benchmark": ["^GSPC"]
    #         },
    #         "static_stats": [{
    #             'net_profit': None, 
    #             'total_return': 10.0, 
    #             'max_drawdown': None, 
    #             'annual_standard_deviation': None, 
    #             'ending_equity': None, 
    #             'total_fees': 2.5, 
    #             'total_trades': 5, 
    #             'num_winning_trades': None, 
    #             'num_lossing_trades': None, 
    #             'avg_win_percent': None, 
    #             'avg_loss_percent': None, 
    #             'percent_profitable': None, 
    #             'profit_and_loss': None,
    #             'profit_factor': None, 
    #             'avg_trade_profit': None, 
    #             'sharpe_ratio': None, 
    #             'sortino_ratio': None, 
    #             'alpha': None, 
    #             'beta': None
    #         }],
    #         "timeseries_stats": [
    #             {
    #                 "timestamp": "2023-12-09T12:00:00Z",
    #                 "equity_value": 10000.0,
    #                 "percent_drawdown": 9.9, 
    #                 "cumulative_return": -0.09, 
    #                 "daily_return": 79.9
    #             },
    #             {
    #                 "timestamp": "2023-12-10T12:00:00Z",
    #                 "equity_value": 10000.0,
    #                 "percent_drawdown": 9.9, 
    #                 "cumulative_return": -0.09, 
    #                 "daily_return": 79.9
    #             }
    #         ],
    #         "trades": [{
    #             "trade_id": 1, 
    #             "leg_id": 1, 
    #             "timestamp": "2023-01-03T00:00:00+0000", 
    #             "ticker": "AAPL", 
    #             "quantity": 4, 
    #             "price": 130.74, 
    #             "cost": -522.96, 
    #             "action": "BUY", 
    #             "fees": 0.0
    #         }],
    #         "signals": [{
    #             "timestamp": "2023-01-03T00:00:00+0000", 
    #             "trade_instructions": [{
    #                 "ticker": "AAPL", 
    #                 "action": "BUY", 
    #                 "trade_id": 1, 
    #                 "leg_id": 1, 
    #                 "weight": 0.05
    #             }, 
    #             {
    #                 "ticker": "MSFT", 
    #                 "action": "SELL", 
    #                 "trade_id": 1, 
    #                 "leg_id": 2, 
    #                 "weight": 0.05
    #             }]
    #         }]
    #     }

    #     response = self.database_client.create_live_session(data)

    #     # Test
    #     actual = self.database_client.get_live_sessions()

    #     # Validate
    #     self.assertNotEqual(actual, None)
    #     self.assertGreater(len(actual), 0)

    # def test_get_specific_live_session(self):
    #     data = {
    #         "parameters": {
    #             "strategy_name": "cointegrationzscore", 
    #             "capital": 100000, 
    #             "data_type": "BAR", 
    #             "train_start": "2018-05-18", 
    #             "train_end": "2023-01-19", 
    #             "test_start": "2023-01-19", 
    #             "test_end": "2024-01-19", 
    #             "tickers": ["HE.n.0", "ZC.n.0"], 
    #             "benchmark": ["^GSPC"]
    #         },
    #         "static_stats": [{
    #             'net_profit': None, 
    #             'total_return': 10.0, 
    #             'max_drawdown': None, 
    #             'annual_standard_deviation': None, 
    #             'ending_equity': None, 
    #             'total_fees': 2.5, 
    #             'total_trades': 5, 
    #             'num_winning_trades': None, 
    #             'num_lossing_trades': None, 
    #             'avg_win_percent': None, 
    #             'avg_loss_percent': None, 
    #             'percent_profitable': None, 
    #             'profit_and_loss': None,
    #             'profit_factor': None, 
    #             'avg_trade_profit': None, 
    #             'sharpe_ratio': None, 
    #             'sortino_ratio': None, 
    #             'alpha': None, 
    #             'beta': None
    #         }],
    #         "timeseries_stats": [
    #             {
    #                 "timestamp": "2023-12-09T12:00:00Z",
    #                 "equity_value": 10000.0,
    #                 "percent_drawdown": 9.9, 
    #                 "cumulative_return": -0.09, 
    #                 "daily_return": 79.9
    #             },
    #             {
    #                 "timestamp": "2023-12-10T12:00:00Z",
    #                 "equity_value": 10000.0,
    #                 "percent_drawdown": 9.9, 
    #                 "cumulative_return": -0.09, 
    #                 "daily_return": 79.9
    #             }
    #         ],
    #         "trades": [{
    #             "trade_id": 1, 
    #             "leg_id": 1, 
    #             "timestamp": "2023-01-03T00:00:00+0000", 
    #             "ticker": "AAPL", 
    #             "quantity": 4, 
    #             "price": 130.74, 
    #             "cost": -522.96, 
    #             "action": "BUY", 
    #             "fees": 0.0
    #         }],
    #         "signals": [{
    #             "timestamp": "2023-01-03T00:00:00+0000", 
    #             "trade_instructions": [{
    #                 "ticker": "AAPL", 
    #                 "action": "BUY", 
    #                 "trade_id": 1, 
    #                 "leg_id": 1, 
    #                 "weight": 0.05
    #             }, 
    #             {
    #                 "ticker": "MSFT", 
    #                 "action": "SELL", 
    #                 "trade_id": 1, 
    #                 "leg_id": 2, 
    #                 "weight": 0.05
    #             }]
    #         }]
    #     }

    #     response = self.database_client.create_live_session(data)
    #     # Test
    #     actual = self.database_client.get_specific_live_session(response['id'])

    #     # Validate
    #     self.assertNotEqual(actual, None)


if __name__ == "__main__":
    unittest.main()

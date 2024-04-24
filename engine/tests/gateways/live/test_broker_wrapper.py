import time
import unittest
from threading import Timer
from ibapi.order import Order
from ibapi.contract import Contract
from ibapi.execution import Execution
from unittest.mock import Mock, patch

from engine.events import ExecutionEvent
from engine.gateways.live.broker_client.wrapper import BrokerApp

from shared.portfolio import AccountDetails, ActiveOrder, EquityDetails, Position
from shared.symbol import Equity, Future, Currency, Venue, Industry, ContractUnits


#TODO: execution Details

class TestBrokerApp(unittest.TestCase):
    def setUp(self):
        self.mock_logger = Mock()
        self.mock_portfolio_server = Mock()
        self.performance_manager = Mock()

        self.broker_app = BrokerApp(logger=self.mock_logger, portfolio_server=self.mock_portfolio_server, performance_manager=self.performance_manager)

    # Basic Validation
    def test_200_error_valid(self):
        # Simulate an error code for contract not found
        self.broker_app.error(reqId=-1, errorCode=200, errorString="Contract not found")
        
        self.mock_logger.critical.assert_called_once_with("200 : Contract not found") # Verify critical log is called with expected message
        self.assertFalse(self.broker_app.is_valid_contract) # Verify is_valid_contract is set to False
        self.assertTrue(self.broker_app.validate_contract_event.is_set()) # Verify validate_contract_event is set

    def test_connectAck_valid(self):
        self.broker_app.connectAck()
        self.mock_logger.info.assert_called_once_with('Established Broker Connection') # Verify critical log is called with expected message
        self.assertFalse(self.broker_app.is_valid_contract) # Verify is_valid_contract is set to False
        self.assertTrue(self.broker_app.connected_event.is_set()) # Verify validate_contract_event is set

    def test_connection_closed(self):
        self.broker_app.connectionClosed()
        self.mock_logger.info.assert_called_once_with('Closed Broker Connection.')

    def test_nextvalidId_valid(self):
        id = 10
        self.broker_app.nextValidId(id)
        
        self.assertEqual(self.broker_app.next_valid_order_id, id)
        self.mock_logger.info.assert_called_once_with(f"Next Valid Id {id}")
        self.assertTrue(self.broker_app.valid_id_event.is_set()) 

    def test_contractDetails(self):
        self.broker_app.contractDetails(10, None)
        self.assertTrue(self.broker_app.is_valid_contract)

    def test_contractDetailsEnd_valid(self):
        self.broker_app.contractDetailsEnd(10)
        
        self.mock_logger.info.assert_called_once_with("Contract Details Received.")
        self.assertTrue(self.broker_app.validate_contract_event.is_set())

    def test_updateAccountValue(self):
        self.broker_app.process_account_updates = Mock()

        test_data = {1:{'key':'FullAvailableFunds', 'val':'100000', 'currency':'USD', 'accountName':'testaccount'}, 
                     2:{'key':'FullInitMarginReq', 'val':'100000', 'currency':'USD', 'accountName':'testaccount'},
                     3:{'key': 'NetLiquidation', 'val':'100000', 'currency':'USD', 'accountName':'testaccount'},
                     4: {'key':'UnrealizedPnL', 'val':'100000', 'currency':'USD', 'accountName':'testaccount'},
                     5:{'key':'FullMaintMarginReq', 'val':'100000', 'currency':'USD', 'accountName':'testaccount'},
                     6:{'key':'Currency', 'val':'USD', 'currency':'USD', 'accountName':'testaccount'}}
        valid_account_info = AccountDetails(FullAvailableFunds = 100000.0, 
                                            FullInitMarginReq =  100000.0,
                                            NetLiquidation = 100000.0,
                                            UnrealizedPnL =  100000.0,
                                            FullMaintMarginReq =  100000.0,
                                            Currency = 'USD') 

        # test
        for key, value in test_data.items():
            self.broker_app.updateAccountValue(value['key'], value['val'], value['currency'], value['accountName'])
        
        #  validate 
        self.assertNotEqual(self.broker_app.account_update_timer,None )
        self.assertEqual(self.broker_app.account_info, valid_account_info)
        self.assertIsInstance(valid_account_info['FullAvailableFunds'], float)
        self.assertIsInstance(valid_account_info['FullInitMarginReq'], float)
        self.assertIsInstance(valid_account_info['NetLiquidation'], float)
        self.assertIsInstance(valid_account_info['UnrealizedPnL'], float)
        self.assertIsInstance(valid_account_info['FullMaintMarginReq'], float)
        self.assertIsInstance(valid_account_info['Currency'], str)
        time.sleep(3)
        self.broker_app.process_account_updates.assert_called_once()

    def test_process_account_updates(self):
        self.mock_portfolio_server.update_account_details = Mock()
        self.broker_app.account_update_timer = True

        # test
        self.broker_app.process_account_updates()

        # validate
        self.assertIn("Timestamp", self.broker_app.account_info.keys())
        self.mock_portfolio_server.update_account_details.assert_called_once_with(self.broker_app.account_info)
        self.assertIsNone(self.broker_app.account_update_timer)
            
    def test_updatePortfolio(self):
        aapl_contract = Contract()
        aapl_contract.symbol = 'AAPL'
        aapl_position = 10
        aapl_market_price = 90.9
        aapl_market_value = 900.9
        aapl_avg_cost = 8.0
        aapl_unrealizedPNL = 100.9
        aapl_realizedPNL = 0.0
        accountName = 'testaccount'
        
        aapl_position_obj = Position(action ='BUY',
                                        avg_cost=aapl_avg_cost,
                                        quantity=aapl_position,
                                        total_cost=aapl_position*aapl_avg_cost,
                                        market_value=aapl_market_price,
                                        quantity_multiplier=1,
                                        price_multiplier=1,
                                        initial_margin=0
                                        )
        
        he_contract = Contract()
        he_contract.symbol = 'HEJ4'
        he_position = -1100
        he_market_price = 9.9
        he_market_value = 9000.09
        he_avg_cost = 8.0
        he_unrealizedPNL = 100.9
        he_realizedPNL = 0.0
        accountName = 'testaccount'


        he_position_obj = Position(action ='SELL',
                                avg_cost=he_avg_cost,
                                quantity=he_position,
                                total_cost=he_position*aapl_avg_cost,
                                market_value=he_market_price,
                                quantity_multiplier=40000,
                                price_multiplier=0.01,
                                initial_margin=4564.17
                                )
        self.broker_app.symbols_map = {'HEJ4' : Future(ticker = "HEJ4",
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
                                    'AAPL' : Equity(ticker="AAPL",
                                                    currency = Currency.USD  ,
                                                    exchange = Venue.NASDAQ  ,
                                                    fees = 0.1,
                                                    initialMargin = 0,
                                                    quantity_multiplier=1,
                                                    price_multiplier=1,
                                                    data_ticker = "AAPL2",
                                                    company_name = "Apple Inc.",
                                                    industry=Industry.TECHNOLOGY,
                                                    market_cap=10000000000.99,
                                                    shares_outstanding=1937476363)}

        positions = {1:aapl_position_obj,2: he_position_obj}
        test_data = {1 : {'contract': aapl_contract, 'position':aapl_position, 'marketPrice':aapl_market_price, 'marketValue': aapl_market_value, 'averageCost': aapl_avg_cost, 'unrealizedPNL':aapl_realizedPNL, 'realizedPNL':aapl_realizedPNL, 'accountName':accountName},
                     2 : {'contract': he_contract, 'position':he_position, 'marketPrice': he_market_price, 'marketValue': he_market_value, 'averageCost': he_avg_cost, 'unrealizedPNL': he_unrealizedPNL, 'realizedPNL': he_realizedPNL, 'accountName': accountName}}
        
        with patch.object(self.broker_app.portfolio_server, 'update_positions') as mock_method:
            for key, value in test_data.items():
                self.broker_app.updatePortfolio(value['contract'], value['position'], value['marketPrice'], value['marketValue'], value['averageCost'], value['unrealizedPNL'], value['realizedPNL'],value['accountName'])
                mock_method.assert_called_with(value['contract'], positions[key])
 
    def test_accountDownloadEnd_valid(self):
        account_info =  { 1 : "1"}
        self.broker_app.account_info = account_info
        self.performance_manager.update_account_log = Mock()
        self.broker_app.process_account_updates = Mock()

        # test
        account_name = 'testname'
        self.broker_app.accountDownloadEnd(account_name)

        # validate
        self.assertIsNone(self.broker_app.account_update_timer)
        self.broker_app.process_account_updates.assert_called_once()
        self.performance_manager.update_account_log.assert_called_once_with(account_info.copy())
        self.mock_logger.info.assert_called_once_with(f"AccountDownloadEnd. Account: {account_name}")
        self.assertTrue(self.broker_app.account_download_event.is_set()) 

    def test_openOrder_valid(self):
        order_id = 10
        contract = Contract()
        contract.symbol = 'AAPL'
        contract.secType = 'STK'
        contract.exchange = 'NASDAQ'

        order = Order()
        order.permId = 10
        order.clientId = 1
        order.account = 'account_name'
        order.action = 'BUY'
        order.orderType = 'MKT'
        order.totalQuantity = 100
        order.cashQty = 100909
        order.lmtPrice = 0
        order.auxPrice = 0

        order_state = Mock()
        order_state.status = 'Cancelled' # or 'Filled'


        valid_order = ActiveOrder(permId = order.permId,
                                    clientId= order.clientId, 
                                    orderId= order_id, 
                                    account= order.account, 
                                    symbol= contract.symbol, 
                                    secType= contract.secType,
                                    exchange= contract.exchange, 
                                    action= order.action, 
                                    orderType= order.orderType,
                                    totalQty= order.totalQuantity, 
                                    cashQty= order.cashQty, 
                                    lmtPrice= order.lmtPrice, 
                                    auxPrice= order.auxPrice, 
                                    status= order_state.status)

        with patch.object(self.mock_portfolio_server, 'update_orders') as mock_update_orders:
            self.broker_app.openOrder(order_id, contract, order, order_state)
            mock_update_orders.assert_called_once_with(valid_order)

    def test_openOrderEnd(self):
        self.broker_app.openOrderEnd()
        self.mock_logger.info.assert_called_once_with(f"Initial Open Orders Received.")
        self.broker_app.open_orders_event.is_set()

    def test_orderStatus(self):
        orderId = 1
        status = 'Submitted' # Options : PendingSubmit, PendingCancel PreSubmitted, Submitted, Cancelled, Filled, Inactive 
        filled = 10
        remaining = 10
        avgFillPrice = 10.90
        permId = 90909
        parentId = 10
        lastFillPrice = 10.90
        clientId = 1
        whyHeld = ""
        mktCapPrice = 19029003

        order_data = ActiveOrder(
            permId = permId,
            orderId =  orderId,
            status =  status, # Options : PendingSubmit, PendingCancel PreSubmitted, Submitted, Cancelled, Filled, Inactive 
            filled =  filled,
            remaining =  remaining,
            avgFillPrice =  avgFillPrice, 
            parentId =  parentId,
            lastFillPrice =  lastFillPrice, 
            whyHeld =  whyHeld, 
            mktCapPrice =  mktCapPrice
        )

        with patch.object(self.mock_portfolio_server, 'update_orders') as mock_method:
            self.broker_app.orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
            self.mock_logger.info.assert_called_once_with(f"Received order status update for orderId {orderId}: {status}")
            mock_method.assert_called_once_with(order_data)

    def test_accountSummary(self):
        test_data = {1:{'tag':'FullAvailableFunds', 'value':'100000', 'currency':'USD', 'account':'testaccount'}, 
                        2:{'tag':'FullInitMarginReq', 'value':'100000', 'currency':'USD', 'account':'testaccount'},
                        3:{'tag': 'NetLiquidation', 'value':'100000', 'currency':'USD', 'account':'testaccount'},
                        4: {'tag':'UnrealizedPnL', 'value':'100000', 'currency':'USD', 'account':'testaccount'},
                        5:{'tag':'FullMaintMarginReq', 'value':'100000', 'currency':'USD', 'account':'testaccount'}}
    
        # test
        for id, value in test_data.items():
            self.broker_app.accountSummary(id, value['account'], value['tag'], value['value'], value['currency'])

        # validate
        valid_account_info = AccountDetails(FullAvailableFunds = 100000.0, 
                                    FullInitMarginReq =  100000.0,
                                    NetLiquidation = 100000.0,
                                    UnrealizedPnL =  100000.0,
                                    FullMaintMarginReq =  100000.0,
                                    Currency = 'USD') 
        self.assertIsInstance(valid_account_info['FullAvailableFunds'], float)
        self.assertIsInstance(valid_account_info['FullInitMarginReq'], float)
        self.assertIsInstance(valid_account_info['NetLiquidation'], float)
        self.assertIsInstance(valid_account_info['UnrealizedPnL'], float)
        self.assertIsInstance(valid_account_info['FullMaintMarginReq'], float)
        self.assertIsInstance(valid_account_info['Currency'], str)

    def test_accountSummaryEnd(self):
        self.performance_manager.update_account_log = Mock()

        # test
        reqId = 10
        self.broker_app.accountSummaryEnd(reqId)
        
        # validate
        self.assertIn("Timestamp", self.broker_app.account_info.keys())
        self.mock_logger.info.assert_called_once_with(f"Account Summary Request Complete: {reqId}")
        self.performance_manager.update_account_log.assert_called_once_with(self.broker_app.account_info.copy())

    def test_execDetails(self):
        reqId = 1
        permId = 109
        contract = Contract()
        contract.symbol = 'AAPL'
        contract.secType = 'STK'
        contract.exchange = 'NASDAQ'

        execution = Execution()
        execution.execId = 11
        execution.time = "20240424 09:54:50 US/Central"
        execution.acctNumber = "128294"
        execution.exchange = 'NASDAQ'
        execution.side = "SLD"

        execution.shares = 1000
        execution.price = 100
        execution.avgPrice = 99.9
        execution.cumQty = 9.9
        execution.orderRef = ""

        execution_data = {
            "timestamp": 1713970490000000000, 
            "ticker": contract.symbol, 
            "quantity": format(execution.shares, 'f'),  # Decimal
            "cumQty": format(execution.cumQty, 'f'),  # Decimal
            "price": execution.price,
            "AvPrice": execution.avgPrice,
            "action": "SELL",
            "cost":0,
            "currency": contract.currency, 
        }

        with patch.object(self.performance_manager, 'update_trades') as mock_method:
            self.broker_app.execDetails(reqId, contract, execution)
            mock_method.assert_called_once_with(execution.execId ,execution_data)


if __name__ == "__main__":
    unittest.main()
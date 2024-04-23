import unittest
from ibapi.order import Order
from ibapi.contract import Contract
from unittest.mock import patch, Mock

from engine.observer import Observer, EventType, Subject
from engine.portfolio import PortfolioServer

from shared.portfolio import Position, AccountDetails, ActiveOrder
from shared.symbol import Future, Equity, Currency, Venue, Industry, ContractUnits
#TODO: edge cases, integration

class TestPortfolioServer(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_symbols_map = {'HEJ4' : Future(ticker = "HEJ4",
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
        self.mock_logger= Mock() 
        self.portfolio_server = PortfolioServer(symbols_map=self.valid_symbols_map, logger=self.mock_logger)

        class ChildObserver(Observer):
            def __init__(self) -> None:
                self.tester = None

            def update(self, subject, event_type: EventType):
                if event_type == EventType.POSITION_UPDATE:
                    self.tester = 1
                elif event_type == EventType.ORDER_UPDATE:
                    self.tester = 2
                elif event_type == EventType.ACCOUNT_DETAIL_UPDATE:
                    self.tester = 3
                elif event_type == EventType.MARKET_EVENT:
                    self.tester = 4
                elif event_type == EventType.RISK_MODEL_UPDATE:
                    self.tester = 5

        # Oberver Pattern 
        self.observer = ChildObserver()

        self.portfolio_server.attach(self.observer, EventType.ACCOUNT_DETAIL_UPDATE)
        self.portfolio_server.attach(self.observer, EventType.POSITION_UPDATE)
        self.portfolio_server.attach(self.observer, EventType.ORDER_UPDATE)
    
    # Basic Validation
    def test_get_active_order_tickers(self):
        self.portfolio_server.pending_positions_update.add("TSLA")
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
        order_state.status = 'PreSubmitted'

        active_order = ActiveOrder(permId = order.permId,
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
        
        self.portfolio_server.active_orders[order.permId] = active_order
        active_order['status'] = 'Submitted'
        self.assertEqual(self.observer.tester, None)
        
        # test
        result = self.portfolio_server.get_active_order_tickers()

        # validate
        expected  = ['AAPL', 'TSLA']
        for i in expected:
            self.assertIn(i, result)

    def test_update_positions_new_valid(self):
        self.portfolio_server.pending_positions_update.add("AAPL")
        contract = Contract()
        contract.symbol = 'AAPL'
        position = Position(action='BUY', 
                            avg_cost=10.9,
                            quantity=100,
                            total_cost=100000,
                            market_value=10000,
                            quantity_multiplier=1,
                            price_multiplier=1,
                            initial_margin=0)
        self.assertEqual(self.observer.tester, None)
        
        
        # Test
        self.portfolio_server.update_positions(contract, position)

        # Validation
        self.assertEqual(self.portfolio_server.positions[contract.symbol], position)
        self.assertEqual(self.observer.tester, 1)
        self.assertEqual(len(self.portfolio_server.pending_positions_update), 0)
        self.mock_logger.info.assert_called_once()

    def test_update_positions_old_valid(self):
        contract = Contract()
        contract.symbol = 'AAPL'
        position = Position(action='BUY', 
                            avg_cost=10.9,
                            quantity=100,
                            total_cost=100000,
                            market_value=10000,
                            quantity_multiplier=1,
                            price_multiplier=1,
                            initial_margin=0)
        
        self.portfolio_server.positions[contract.symbol] = position
        self.assertEqual(self.observer.tester, None)
        
        # Test
        response = self.portfolio_server.update_positions(contract, position)

        # Validation
        self.assertEqual(response, None)
        self.assertEqual(self.portfolio_server.positions[contract.symbol], position)
        self.assertEqual(len(self.portfolio_server.positions), 1)
        self.assertFalse(self.mock_logger.info.called)
        self.assertEqual(self.observer.tester, None)

    def test_output_positions(self):
        contract = Contract()
        contract.symbol = 'AAPL'
        position = Position(action='BUY', 
                    avg_cost=10.9,
                    quantity=100,
                    total_cost=100000,
                    market_value=10000,
                    quantity_multiplier=1,
                    price_multiplier=1,
                    initial_margin=0)
        
        # Test
        self.portfolio_server.update_positions(contract, position)

        # Validation
        self.mock_logger.info.assert_called_once_with("\nPositions Updated: \n AAPL: {'action': 'BUY', 'avg_cost': 10.9, 'quantity': 100, 'total_cost': 100000, 'market_value': 10000, 'quantity_multiplier': 1, 'price_multiplier': 1, 'initial_margin': 0} \n")

    def test_update_account_details_valid(self):
        account_info = AccountDetails(FullAvailableFunds = 100000.0, 
                                        FullInitMarginReq =  100000.0,
                                        NetLiquidation = 100000.0,
                                        UnrealizedPnL =  100000.0,
                                        FullMaintMarginReq =  100000.0,
                                        Currency = 'USD') 
        self.assertEqual(self.observer.tester, None)
        
        # Test
        self.portfolio_server.update_account_details(account_info)

        # Validation
        self.assertEqual(self.portfolio_server.account, account_info)
        self.assertEqual(self.portfolio_server.capital, account_info['FullAvailableFunds'])
        self.assertEqual(self.observer.tester, 3)
        self.mock_logger.info.assert_called_once()
    
    def test_output_account(self):
        account_info = AccountDetails(FullAvailableFunds = 100000.0, 
                                FullInitMarginReq =  100000.0,
                                NetLiquidation = 100000.0,
                                UnrealizedPnL =  100000.0,
                                FullMaintMarginReq =  100000.0,
                                Currency = 'USD') 

        # Test
        self.portfolio_server.update_account_details(account_info)

        # Validation
        self.mock_logger.info.assert_called_once_with('\nAccount Updated: \n FullAvailableFunds : 100000.0 \n FullInitMarginReq : 100000.0 \n NetLiquidation : 100000.0 \n UnrealizedPnL : 100000.0 \n FullMaintMarginReq : 100000.0 \n Currency : USD \n')
        
    def test_update_orders_new_valid(self):
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
        order_state.status = 'PreSubmitted'

        active_order = ActiveOrder(permId = order.permId,
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
        self.assertEqual(self.observer.tester, None)
        
        # Test
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.assertEqual(self.portfolio_server.active_orders[order.permId], active_order)
        self.assertEqual(self.observer.tester, 2)
        self.mock_logger.info.assert_called_once()

    def test_update_orders_update_valid(self):
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
        order_state.status = 'PreSubmitted'

        active_order = ActiveOrder(permId = order.permId,
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
        
        self.portfolio_server.active_orders[order.permId] = active_order
        active_order['status'] = 'Submitted'
        self.assertEqual(self.observer.tester, None)

        # Test
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.assertEqual(self.portfolio_server.active_orders[order.permId], active_order)
        self.assertEqual(len(self.portfolio_server.active_orders), 1)
        self.assertEqual(self.portfolio_server.active_orders[order.permId]['status'], 'Submitted')
        self.assertEqual(self.observer.tester, 2)

        self.mock_logger.info.assert_called_once()

    def test_update_orders_filled_valid(self):
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
        order_state.status = 'PreSubmitted'

        active_order = ActiveOrder(permId = order.permId,
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
        
        self.portfolio_server.active_orders[order.permId] = active_order
        self.assertEqual(len(self.portfolio_server.active_orders), 1) # ensure order in portfolio server active orders
        active_order['status'] = 'Filled'
        self.assertEqual(self.observer.tester, None)

        # Test
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.assertEqual(self.portfolio_server.active_orders, {})
        self.assertEqual(len(self.portfolio_server.active_orders), 0)
        self.assertEqual(self.observer.tester, 2)
        self.assertIn("AAPL", self.portfolio_server.pending_positions_update)
        self.mock_logger.info.assert_called_once()

    def test_update_orders_cancelled_valid(self):
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
        order_state.status = 'PreSubmitted'

        active_order = ActiveOrder(permId = order.permId,
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
        
        self.portfolio_server.active_orders[order.permId] = active_order
        self.assertEqual(len(self.portfolio_server.active_orders), 1)  # ensure order in portfolio server active orders
        active_order['status'] = 'Cancelled'
        self.assertEqual(self.observer.tester, None)

        # Tests
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.assertEqual(self.portfolio_server.active_orders, {})
        self.assertEqual(len(self.portfolio_server.active_orders), 0)
        self.assertEqual(self.observer.tester, 2)
        self.mock_logger.info.assert_called_once()

    def test_output_orders(self):
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
        order_state.status = 'PreSubmitted'

        active_order = ActiveOrder(permId = order.permId,
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
        
        # Tests
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.mock_logger.info.assert_called_once_with("\nOrder Updated: \n {'permId': 10, 'clientId': 1, 'orderId': 10, 'account': 'account_name', 'symbol': 'AAPL', 'secType': 'STK', 'exchange': 'NASDAQ', 'action': 'BUY', 'orderType': 'MKT', 'totalQty': 100, 'cashQty': 100909, 'lmtPrice': 0, 'auxPrice': 0, 'status': 'PreSubmitted'} \n")

if __name__ == "__main__":
    unittest.main()
import unittest
import numpy as np
from ibapi.order import Order
from ibapi.contract import Contract
from unittest.mock import patch, Mock
from midas.engine.portfolio import PortfolioServer
from midas.shared.active_orders import ActiveOrder
from midas.shared.account import Account
from midas.engine.observer import Observer, EventType, Subject
from midas.shared.positions import EquityPosition, FuturePosition
from midas.shared.symbol import Future, Equity, Currency, Venue, Industry, ContractUnits


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

class TestPortfolioServer(unittest.TestCase):
    def setUp(self) -> None:
        # Test symbols
        self.symbols_map = {'HEJ4' : Future(ticker = "HEJ4",
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
                                    'AAPL' : Equity(ticker="AAPL",
                                                    currency = Currency.USD  ,
                                                    exchange = Venue.NASDAQ  ,
                                                    fees = 0.1,
                                                    initial_margin = 0,
                                                    quantity_multiplier=1,
                                                    price_multiplier=1,
                                                    data_ticker = "AAPL2",
                                                    company_name = "Apple Inc.",
                                                    industry=Industry.TECHNOLOGY,
                                                    market_cap=10000000000.99,
                                                    shares_outstanding=1937476363)}
        
        # Portfolio server instance
        self.mock_logger= Mock() 
        self.portfolio_server = PortfolioServer(symbols_map=self.symbols_map, logger=self.mock_logger)

        # Oberver Pattern 
        self.observer = ChildObserver()
        self.portfolio_server.attach(self.observer, EventType.ACCOUNT_DETAIL_UPDATE)
        self.portfolio_server.attach(self.observer, EventType.POSITION_UPDATE)
        self.portfolio_server.attach(self.observer, EventType.ORDER_UPDATE)
    
    # Basic Validation
    def test_get_active_order_tickers(self):
        self.portfolio_server.pending_positions_update.add("TSLA")
        
        # Order data
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
        
        # Create order
        active_order = ActiveOrder(
            permId = order.permId,
            clientId= order.clientId, 
            parentId=order.parentId,
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
            status= order_state.status
        )
        
        # Add order to portfolio server
        self.portfolio_server.active_orders[order.permId] = active_order
        active_order.status = 'Submitted'
        self.assertEqual(self.observer.tester, None)
        
        # Test
        result = self.portfolio_server.get_active_order_tickers()

        # Validate
        expected  = ['AAPL', 'TSLA']
        for i in expected:
            self.assertIn(i, result)

    def test_update_positions_new_valid(self):
        self.portfolio_server.pending_positions_update.add("AAPL")
        
        # Position data
        contract = Contract()
        contract.symbol = 'AAPL'
        position = EquityPosition(
            action = 'BUY',
            avg_price = 10.90,
            quantity = 100,
            quantity_multiplier = 10,
            price_multiplier = 0.01,
            market_price = 12,
        )
        self.assertEqual(self.observer.tester, None)
        
        # Test
        self.portfolio_server.update_positions(contract, position)

        # Validate
        self.assertEqual(self.portfolio_server.positions[contract.symbol], position)
        self.assertEqual(self.observer.tester, 1)
        self.assertEqual(len(self.portfolio_server.pending_positions_update), 0)
        self.mock_logger.info.assert_called_once()

    def test_update_positions_old_valid(self):
        # Postion data
        contract = Contract()
        contract.symbol = 'AAPL'
        position =EquityPosition(
            action = 'BUY',
            avg_price = 10.90,
            quantity = 100,
            quantity_multiplier = 10,
            price_multiplier = 0.01,
            market_price = 12,
        )
        
        # Add old position to portfolio server
        self.portfolio_server.positions[contract.symbol] = position
        self.assertEqual(self.observer.tester, None)
        
        # Test
        response = self.portfolio_server.update_positions(contract, position)

        # Validate
        self.assertEqual(response, None)
        self.assertEqual(self.portfolio_server.positions[contract.symbol], position)
        self.assertEqual(len(self.portfolio_server.positions), 1)
        self.assertTrue(self.mock_logger.info.assert_called)
        self.assertEqual(self.observer.tester, 1)

    def test_updated_positions_zero_quantity(self):
        # Old postion
        contract = Contract()
        contract.symbol = 'AAPL'
        position = EquityPosition(
            action = 'BUY',
            avg_price = 10.90,
            quantity = 100,
            quantity_multiplier = 10,
            price_multiplier = 0.01,
            market_price = 12,
        )
        # Add old position to portfolio server
        self.portfolio_server.positions[contract.symbol] = position
        self.assertEqual(self.observer.tester, None)
        
        # Test
        new_position = EquityPosition(
            action = 'BUY',
            avg_price = 10.90,
            quantity = 0,
            quantity_multiplier = 10,
            price_multiplier = 0.01,
            market_price = 12,
        )
        self.portfolio_server.update_positions(contract, new_position)

        # Validation
        self.assertEqual(self.portfolio_server.positions, {})
        self.assertEqual(self.observer.tester, 1)
        self.assertEqual(len(self.portfolio_server.pending_positions_update), 0)
        self.mock_logger.info.assert_called_once()
    
    def test_output_positions(self):
        # Postion data
        contract = Contract()
        contract.symbol = 'AAPL'
        position = EquityPosition(
            action = 'BUY',
            avg_price = 10.90,
            quantity = 100,
            quantity_multiplier = 10,
            price_multiplier = 0.01,
            market_price = 12,
        )

        # Test
        self.portfolio_server.update_positions(contract, position)

        # Validation
        self.mock_logger.info.assert_called_once_with('\nPOSITIONS UPDATED: \nAAPL:\n  Action: BUY\n  Average Price: 10.9\n  Quantity: 100\n  Price Multiplier: 0.01\n  Quantity Multiplier: 10\n  Initial Value: 10900.0\n  Initial Cost: 10900.0\n  Market Price: 12\n  Market Value: 12000\n  Unrealized P&L: 1100.0\n  Liquidation Value: 12000\n  Margin Required: 0\n\n')

    def test_update_account_details_valid(self):
        # Account data
        account_info = Account(     
                                timestamp=np.uint64(16777700000000),
                                full_available_funds= 100000.0, 
                                full_init_margin_req= 100000.0,
                                net_liquidation= 100000.0,
                                unrealized_pnl=  100000.0,
                                full_maint_margin_req=  100000.0,
                                currency='USD'
                            ) 
        self.assertEqual(self.observer.tester, None)
        
        # Test
        self.portfolio_server.update_account_details(account_info)

        # Validation
        self.assertEqual(self.portfolio_server.account, account_info)
        self.assertEqual(self.portfolio_server.capital, account_info.full_available_funds)
        self.assertEqual(self.observer.tester, 3)
        self.mock_logger.info.assert_called_once()
    
    def test_update_orders_new_valid(self):
        # Order data
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

        # Create order
        active_order = ActiveOrder(
            permId = order.permId,
            clientId= order.clientId, 
            parentId=order.parentId,
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
            status= order_state.status
        )
        self.assertEqual(self.observer.tester, None)
        
        # Test
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.assertEqual(self.portfolio_server.active_orders[order.permId], active_order)
        self.assertEqual(self.observer.tester, 2)
        self.mock_logger.info.assert_called_once()

    def test_update_orders_update_valid(self):
        # Old Order
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

        # Create order
        active_order = ActiveOrder(
            permId = order.permId,
            clientId= order.clientId, 
            orderId= order_id, 
            parentId=order.parentId,
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
            status= order_state.status
        )
        # Add order to portfolio server
        self.portfolio_server.active_orders[order.permId] = active_order

        # Update order status
        active_order.status = 'Submitted'
        self.assertEqual(self.observer.tester, None)

        # Test
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.assertEqual(self.portfolio_server.active_orders[order.permId], active_order)
        self.assertEqual(len(self.portfolio_server.active_orders), 1)
        self.assertEqual(self.portfolio_server.active_orders[order.permId].status, 'Submitted')
        self.assertEqual(self.observer.tester, 2)

        self.mock_logger.info.assert_called_once()

    def test_update_orders_filled_valid(self):
        # Old order data
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

        active_order = ActiveOrder(
            permId = order.permId,
            clientId= order.clientId, 
            orderId= order_id, 
            parentId=order.parentId,
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
            status= order_state.status
        )

        # Add order to porfolio server
        self.portfolio_server.active_orders[order.permId] = active_order
        self.assertEqual(len(self.portfolio_server.active_orders), 1) # ensure order in portfolio server active orders

        # Update order status to filled 
        active_order.status = 'Filled'
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
        # Old order data
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

        active_order = ActiveOrder(
            permId = order.permId,
            clientId= order.clientId, 
            parentId=order.parentId,
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
            status= order_state.status
        )
        
        # Add order to portfolio server
        self.portfolio_server.active_orders[order.permId] = active_order
        self.assertEqual(len(self.portfolio_server.active_orders), 1)  # ensure order in portfolio server active orders

        # Updated order status
        active_order.status = 'Cancelled'
        self.assertEqual(self.observer.tester, None)

        # Test
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.assertEqual(self.portfolio_server.active_orders, {})
        self.assertEqual(len(self.portfolio_server.active_orders), 0)
        self.assertEqual(self.observer.tester, 2)
        self.mock_logger.info.assert_called_once()

    def test_output_orders(self):
        # Order data
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

        active_order = ActiveOrder(
            permId = order.permId,
            clientId= order.clientId, 
            parentId=order.parentId,
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
            status= order_state.status
        )
        
        # Tests
        self.portfolio_server.update_orders(active_order)

        # Validation
        self.mock_logger.info.assert_called_once_with('\nORDERS UPDATED: \n10:\n  orderId: 10\n  symbol: AAPL\n  action: BUY\n  orderType: MKT\n  totalQty: 100\n  lmtPrice: 0\n  auxPrice: 0\n  status: PreSubmitted\n  filled: None\n  remaining: None\n  avgFillPrice: None\n  lastFillPrice: None\n  whyHeld: None\n \n')

if __name__ == "__main__":
    unittest.main()

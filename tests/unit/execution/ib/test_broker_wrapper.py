from decimal import Decimal
import time
import unittest
import datetime
from ibapi.order import Order
from ibapi.contract import Contract
from ibapi.execution import Execution
from unittest.mock import Mock

from midastrader.structs.active_orders import ActiveOrder
from midastrader.structs.account import Account
from midastrader.structs.positions import EquityPosition, FuturePosition
from midastrader.structs.symbol import SymbolMap
from midastrader.structs.trade import Trade
from midastrader.message_bus import MessageBus, EventType
from midastrader.execution.adaptors.ib.wrapper import BrokerApp
from midastrader.structs.events import TradeEvent
from midastrader.structs.symbol import (
    Equity,
    Currency,
    Venue,
    Future,
    Industry,
    ContractUnits,
    SecurityType,
    FuturesMonth,
    TradingSession,
)


class TestBrokerApp(unittest.TestCase):
    def setUp(self):
        # Test symbols
        hogs = Future(
            instrument_id=1,
            broker_ticker="HEJ4",
            data_ticker="HE",
            midas_ticker="HE.n.0",
            security_type=SecurityType.FUTURE,
            fees=0.85,
            currency=Currency.USD,
            exchange=Venue.CME,
            initial_margin=4564.17,
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
            slippage_factor=10,
            lastTradeDateOrContractMonth="202404",
            trading_sessions=TradingSession(
                day_open=datetime.time(9, 0), day_close=datetime.time(14, 0)
            ),
            expr_months=[FuturesMonth.G, FuturesMonth.J, FuturesMonth.Z],
            term_day_rule="nth_business_day_10",
            market_calendar="CMEGlobex_Lean_Hog",
        )
        aapl = Equity(
            instrument_id=2,
            broker_ticker="AAPL",
            data_ticker="AAPL2",
            midas_ticker="AAPL",
            security_type=SecurityType.STOCK,
            currency=Currency.USD,
            exchange=Venue.NASDAQ,
            fees=0.1,
            initial_margin=0,
            quantity_multiplier=1,
            price_multiplier=1,
            company_name="Apple Inc.",
            industry=Industry.TECHNOLOGY,
            market_cap=10000000000.99,
            shares_outstanding=1937476363,
            slippage_factor=10,
            trading_sessions=TradingSession(
                day_open=datetime.time(9, 0), day_close=datetime.time(14, 0)
            ),
        )

        self.symbols_map = SymbolMap()
        self.symbols_map.add_symbol(hogs)
        self.symbols_map.add_symbol(aapl)

        # BrokerApp instance
        self.bus = MessageBus()
        self.broker_app = BrokerApp(self.symbols_map, self.bus)

    # Basic Validation
    def test_200_error_valid(self):
        # Simulate an error code for contract not found
        # Test
        self.broker_app.error(
            reqId=-1, errorCode=200, errorString="Contract not found"
        )

        # Validate
        self.assertFalse(
            self.broker_app.is_valid_contract
        )  # Verify is_valid_contract is set to False
        self.assertTrue(
            self.broker_app.validate_contract_event.is_set()
        )  # Verify validate_contract_event is set

    def test_connectAck_valid(self):
        # Test
        self.broker_app.connectAck()

        # Validate
        self.assertFalse(
            self.broker_app.is_valid_contract
        )  # Verify is_valid_contract is set to False
        self.assertTrue(
            self.broker_app.connected_event.is_set()
        )  # Verify validate_contract_event is set

    def test_nextvalidId_valid(self):
        id = 10

        # Test
        self.broker_app.nextValidId(id)

        # Validate
        self.assertEqual(self.broker_app.next_valid_order_id, id)
        self.assertTrue(self.broker_app.valid_id_event.is_set())

    def test_contractDetails(self):
        # Test
        self.broker_app.contractDetails(10, Mock())

        # Validate
        self.assertTrue(self.broker_app.is_valid_contract)

    def test_contractDetailsEnd_valid(self):
        # Test
        self.broker_app.contractDetailsEnd(10)

        # Validate
        self.assertTrue(self.broker_app.validate_contract_event.is_set())

    def test_updateAccountValue(self):
        self.broker_app.process_account_updates = Mock()

        test_data = {
            1: {
                "key": "FullAvailableFunds",
                "val": "100000",
                "currency": "USD",
                "accountName": "testaccount",
            },
            2: {
                "key": "FullInitMarginReq",
                "val": "100000",
                "currency": "USD",
                "accountName": "testaccount",
            },
            3: {
                "key": "NetLiquidation",
                "val": "100000",
                "currency": "USD",
                "accountName": "testaccount",
            },
            4: {
                "key": "UnrealizedPnL",
                "val": "100000",
                "currency": "USD",
                "accountName": "testaccount",
            },
            5: {
                "key": "FullMaintMarginReq",
                "val": "100000",
                "currency": "USD",
                "accountName": "testaccount",
            },
            6: {
                "key": "Currency",
                "val": "USD",
                "currency": "USD",
                "accountName": "testaccount",
            },
        }

        # Test
        for key, value in test_data.items():
            self.broker_app.updateAccountValue(
                value["key"],
                value["val"],
                value["currency"],
                value["accountName"],
            )

        # Expected
        expected_account_info = Account(
            timestamp=0,
            full_available_funds=100000.0,
            full_init_margin_req=100000.0,
            net_liquidation=100000.0,
            unrealized_pnl=100000.0,
            full_maint_margin_req=100000.0,
            excess_liquidity=0,
            currency="USD",
            buying_power=0.0,
            futures_pnl=0.0,
            total_cash_balance=0.0,
        )

        # Validate
        self.assertNotEqual(self.broker_app.account_update_timer, None)
        self.assertEqual(
            self.broker_app.account_info.full_available_funds,
            expected_account_info.full_available_funds,
        )
        self.assertEqual(
            self.broker_app.account_info.full_maint_margin_req,
            expected_account_info.full_maint_margin_req,
        )
        self.assertEqual(
            self.broker_app.account_info.net_liquidation,
            expected_account_info.net_liquidation,
        )
        self.assertEqual(
            self.broker_app.account_info.unrealized_pnl,
            expected_account_info.unrealized_pnl,
        )
        self.assertEqual(
            self.broker_app.account_info.full_init_margin_req,
            expected_account_info.full_init_margin_req,
        )
        self.assertEqual(
            self.broker_app.account_info.currency,
            expected_account_info.currency,
        )
        time.sleep(3)
        self.broker_app.process_account_updates.assert_called_once()

    def test_process_account_updates(self):
        # Test
        self.bus.publish = Mock()
        self.broker_app.process_account_updates()

        # Validate
        calls = self.bus.publish.call_args_list

        # Validate the first call
        first_call_args = calls[0][0]
        self.assertEqual(first_call_args[0], EventType.ACCOUNT_UPDATE)
        self.assertEqual(first_call_args[1], self.broker_app.account_info)

        # Validate the second call
        second_call_args = calls[1][0]
        self.assertEqual(second_call_args[0], EventType.ACCOUNT_UPDATE_LOG)
        self.assertEqual(second_call_args[1], self.broker_app.account_info)
        self.assertTrue(self.broker_app.account_info.timestamp > 0)
        self.assertIsNone(self.broker_app.account_update_timer)

    def test_updatePortfolio(self):
        # Test positions1
        aapl_contract = Contract()
        aapl_contract.symbol = "AAPL"
        aapl_position = 10.0
        aapl_market_price = 90.9
        aapl_market_value = 900.9
        aapl_avg_cost = 8.0
        aapl_realizedPNL = 0.0
        accountName = "testaccount"

        aapl_position_obj = EquityPosition(
            action="BUY",
            avg_price=aapl_avg_cost,
            quantity=aapl_position,
            quantity_multiplier=1,
            price_multiplier=1,
            market_price=aapl_market_price,
        )

        # Test positions2
        he_contract = Contract()
        he_contract.symbol = "HEJ4"
        he_position = -1100.0
        he_market_price = 9.9
        he_market_value = 9000.09
        he_avg_cost = 8.0
        he_unrealizedPNL = 100.9
        he_realizedPNL = 0.0
        accountName = "testaccount"

        he_position_obj = FuturePosition(
            action="SELL",
            avg_price=he_avg_cost / (0.01 * 40000),
            quantity=he_position,
            quantity_multiplier=40000,
            price_multiplier=0.01,
            market_price=he_market_price / 0.01,
            initial_margin=4564.17,
        )

        # Test data
        test_data = {
            "AAPL": {
                "contract": aapl_contract,
                "position": aapl_position,
                "marketPrice": aapl_market_price,
                "marketValue": aapl_market_value,
                "averageCost": aapl_avg_cost,
                "unrealizedPNL": aapl_realizedPNL,
                "realizedPNL": aapl_realizedPNL,
                "accountName": accountName,
            },
            "HEJ4": {
                "contract": he_contract,
                "position": he_position,
                "marketPrice": he_market_price,
                "marketValue": he_market_value,
                "averageCost": he_avg_cost,
                "unrealizedPNL": he_unrealizedPNL,
                "realizedPNL": he_realizedPNL,
                "accountName": accountName,
            },
        }

        # Expected
        positions = {"AAPL": aapl_position_obj, "HEJ4": he_position_obj}
        self.bus.publish = Mock()

        for key, value in test_data.items():
            # Test
            self.broker_app.updatePortfolio(
                value["contract"],
                value["position"],
                value["marketPrice"],
                value["marketValue"],
                value["averageCost"],
                value["unrealizedPNL"],
                value["realizedPNL"],
                value["accountName"],
            )

            # Validate
            args = self.bus.publish.call_args[0]

            # Validate the first call
            self.assertEqual(args[0], EventType.POSITION_UPDATE)
            self.assertEqual(args[1][0], self.symbols_map.get_id(key))
            self.assertEqual(args[1][1], positions[key])

    def test_accountDownloadEnd_valid(self):
        self.broker_app.process_account_updates = Mock()

        # Test
        account_name = "testname"
        self.broker_app.accountDownloadEnd(account_name)

        # Validate
        self.assertIsNone(self.broker_app.account_update_timer)
        self.broker_app.process_account_updates.assert_called_once()
        self.assertTrue(self.broker_app.account_download_event.is_set())

    def test_openOrder_valid(self):
        # Order data
        order_id = 10
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "NASDAQ"

        order = Order()
        order.permId = 10
        order.clientId = 1
        order.account = "account_name"
        order.action = "BUY"
        order.orderType = "MKT"
        order.totalQuantity = Decimal(100)
        order.cashQty = 100909
        order.lmtPrice = 0
        order.auxPrice = 0

        order_state = Mock()
        order_state.status = "Cancelled"  # or 'Filled'

        # Order dict
        instruement = self.symbols_map.get_id(contract.symbol)
        valid_order = ActiveOrder(
            permId=order.permId,
            clientId=order.clientId,
            parentId=order.parentId,
            orderId=order_id,
            account=order.account,
            instrument=instruement,
            secType=contract.secType,
            exchange=contract.exchange,
            action=order.action,
            orderType=order.orderType,
            totalQty=float(order.totalQuantity),
            cashQty=order.cashQty,
            lmtPrice=order.lmtPrice,
            auxPrice=order.auxPrice,
            status=order_state.status,
        )

        # Test
        self.bus.publish = Mock()
        self.broker_app.openOrder(order_id, contract, order, order_state)

        # Validate
        self.assertEqual(self.bus.publish.call_count, 1)

        # Access all calls made to publish
        args = self.bus.publish.call_args[0]

        # Validate the first call
        self.assertEqual(args[0], EventType.ORDER_UPDATE)
        self.assertEqual(args[1], valid_order)

    def test_openOrderEnd(self):
        # Test
        self.broker_app.openOrderEnd()

        # Validate
        self.broker_app.open_orders_event.is_set()

    def test_orderStatus(self):
        # Order data
        orderId = 1
        status = "Submitted"  # Options : PendingSubmit, PendingCancel PreSubmitted, Submitted, Cancelled, Filled, Inactive
        filled = 10.0
        remaining = 10.0
        avgFillPrice = 10.90
        permId = 90909
        parentId = 10
        lastFillPrice = 10.90
        clientId = 1
        whyHeld = ""
        mktCapPrice = 19029003

        # Order dict
        order_data = ActiveOrder(
            permId=permId,
            parentId=parentId,
            clientId=clientId,
            orderId=orderId,
            status=status,  # Options : PendingSubmit, PendingCancel PreSubmitted, Submitted, Cancelled, Filled, Inactive
            filled=filled,
            remaining=remaining,
            avgFillPrice=avgFillPrice,
            lastFillPrice=lastFillPrice,
            whyHeld=whyHeld,
            mktCapPrice=mktCapPrice,
        )

        # Test
        self.bus.publish = Mock()
        self.broker_app.orderStatus(
            orderId,
            status,
            Decimal(filled),
            Decimal(remaining),
            avgFillPrice,
            permId,
            parentId,
            lastFillPrice,
            clientId,
            whyHeld,
            mktCapPrice,
        )

        # Validate
        self.assertEqual(self.bus.publish.call_count, 1)

        # Access all calls made to publish
        args = self.bus.publish.call_args[0]

        # Validate the first call
        self.assertEqual(args[0], EventType.ORDER_UPDATE)
        self.assertEqual(args[1], order_data)

    def test_accountSummary(self):
        test_data = {
            1: {
                "tag": "FullAvailableFunds",
                "value": "100000",
                "currency": "USD",
                "account": "testaccount",
            },
            2: {
                "tag": "FullInitMarginReq",
                "value": "100000",
                "currency": "USD",
                "account": "testaccount",
            },
            3: {
                "tag": "NetLiquidation",
                "value": "100000",
                "currency": "USD",
                "account": "testaccount",
            },
            4: {
                "tag": "UnrealizedPnL",
                "value": "100000",
                "currency": "USD",
                "account": "testaccount",
            },
            5: {
                "tag": "FullMaintMarginReq",
                "value": "100000",
                "currency": "USD",
                "account": "testaccount",
            },
        }

        # Test
        for id, value in test_data.items():
            self.broker_app.accountSummary(
                id,
                value["account"],
                value["tag"],
                value["value"],
                value["currency"],
            )

        # Expected
        expected_account_info = Account(
            timestamp=0,
            full_available_funds=100000.0,
            full_init_margin_req=100000.0,
            net_liquidation=100000.0,
            unrealized_pnl=100000.0,
            full_maint_margin_req=100000.0,
            currency="USD",
        )
        # Validate
        self.assertEqual(
            self.broker_app.account_info.full_available_funds,
            expected_account_info.full_available_funds,
        )
        self.assertEqual(
            self.broker_app.account_info.full_maint_margin_req,
            expected_account_info.full_maint_margin_req,
        )
        self.assertEqual(
            self.broker_app.account_info.net_liquidation,
            expected_account_info.net_liquidation,
        )
        self.assertEqual(
            self.broker_app.account_info.unrealized_pnl,
            expected_account_info.unrealized_pnl,
        )
        self.assertEqual(
            self.broker_app.account_info.full_init_margin_req,
            expected_account_info.full_init_margin_req,
        )
        self.assertEqual(
            self.broker_app.account_info.currency,
            expected_account_info.currency,
        )

    def test_accountSummaryEnd(self):
        # Test
        self.bus.publish = Mock()
        reqId = 10
        self.broker_app.accountSummaryEnd(reqId)

        # Validate
        self.assertEqual(self.bus.publish.call_count, 2)

        # Access all calls made to publish
        calls = self.bus.publish.call_args_list

        # Validate the first call
        first_call_args = calls[0][0]
        self.assertEqual(first_call_args[0], EventType.ACCOUNT_UPDATE)
        self.assertEqual(first_call_args[1], self.broker_app.account_info)

        # Validate the second call
        second_call_args = calls[1][0]
        self.assertEqual(second_call_args[0], EventType.ACCOUNT_UPDATE_LOG)
        self.assertEqual(second_call_args[1], self.broker_app.account_info)

    def test_execDetails(self):
        # Execution details
        reqId = 1
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "NASDAQ"

        execution = Execution()
        execution.execId = "11"
        execution.time = "20240424 09:54:50 US/Central"
        execution.acctNumber = "128294"
        execution.exchange = "NASDAQ"
        execution.side = "SLD"

        execution.shares = Decimal(1000)
        execution.price = 100.0
        execution.avgPrice = 99.9
        execution.cumQty = Decimal(9.9)
        execution.orderRef = ""

        # Execution dict
        instrument = self.symbols_map.get_id(contract.symbol)
        if instrument:
            execution_data = Trade(
                timestamp=1713970490000000000,
                trade_id=execution.orderId,
                signal_id=0,
                instrument=instrument,
                quantity=float(execution.shares),
                avg_price=float(execution.price),
                trade_value=float(execution.price) * float(execution.shares),
                trade_cost=float(execution.price) * float(execution.shares),
                action="SELL",
                fees=float(0.0),
            )
            event = TradeEvent("11", execution_data)

            # Test
            self.bus.publish = Mock()
            self.broker_app.execDetails(reqId, contract, execution)

            # Validate
            self.assertEqual(self.bus.publish.call_count, 1)

            # Access all calls made to publish
            args = self.bus.publish.call_args[0]

            # Validate the first call
            self.assertEqual(args[0], EventType.TRADE_UPDATE)
            self.assertEqual(args[1], event)


if __name__ == "__main__":
    unittest.main()

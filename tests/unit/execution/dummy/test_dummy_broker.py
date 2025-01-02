import unittest
import threading
from time import sleep
from mbn import OhlcvMsg
from datetime import time
from unittest.mock import Mock, MagicMock
from ibapi.contract import Contract

from midas.structs.trade import Trade
from midas.structs.events import OrderEvent
from midas.structs.account import Account
from midas.structs.orders import Action, MarketOrder
from midas.execution.adaptors.dummy.dummy_broker import DummyBroker
from midas.structs.symbol import SymbolMap
from midas.structs.events import TradeEvent
from midas.message_bus import MessageBus, EventType
from midas.utils.logger import SystemLogger
from midas.structs.positions import FuturePosition, EquityPosition
from midas.core.order_book import OrderBook
from midas.structs.symbol import (
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


class TestDummyClient(unittest.TestCase):
    def setUp(self) -> None:
        # Test symbols
        self.hogs = Future(
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
                day_open=time(9, 0), day_close=time(14, 0)
            ),
            expr_months=[FuturesMonth.G, FuturesMonth.J, FuturesMonth.Z],
            term_day_rule="nth_business_day_10",
            market_calendar="CMEGlobex_Lean_Hog",
        )
        self.aapl = Equity(
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
                day_open=time(9, 0), day_close=time(14, 0)
            ),
        )

        self.symbols_map = SymbolMap()
        self.symbols_map.add_symbol(self.hogs)
        self.symbols_map.add_symbol(self.aapl)

        # Mock Logger
        self.logger = SystemLogger()
        self.logger.get_logger = MagicMock()

        # Dummybroker instance
        self.capital = 100000
        self.bus = MessageBus()
        self.broker = DummyBroker(self.symbols_map, self.bus, self.capital)
        self.order_book = OrderBook.get_instance()

    # Basic Validation
    def test_process_orderbook_update(self):
        self.broker._update_account = Mock()
        self.broker.return_equity_value = Mock()

        # Test
        threading.Thread(target=self.broker.process, daemon=True).start()
        self.bus.publish(EventType.UPDATE_EQUITY, True)
        sleep(1)

        # Validate
        self.assertTrue(self.broker._update_account.called)
        self.assertTrue(self.broker.return_equity_value.called)
        self.assertEqual(self.bus.get_flag(EventType.UPDATE_EQUITY), False)

    def test_process_eod(self):
        self.broker._update_account = Mock()
        self.broker.mark_to_market = Mock()
        self.broker.check_margin_call = Mock()

        # Test
        threading.Thread(target=self.broker.process, daemon=True).start()
        self.bus.publish(EventType.EOD, True)
        sleep(1)

        # Validate
        self.assertTrue(self.broker._update_account.called)
        self.assertTrue(self.broker.mark_to_market.called)
        self.assertTrue(self.broker.check_margin_call.called)
        self.assertEqual(self.bus.get_flag(EventType.EOD), False)

    def test_process_trades(self):
        # Mock order
        timestamp = 1651500000
        action = Action.LONG
        trade_id = 2
        leg_id = 6
        order = MarketOrder(action, 10)
        contract = Contract()

        event = OrderEvent(
            timestamp=timestamp,
            trade_id=trade_id,
            leg_id=leg_id,
            action=action,
            order=order,
            contract=contract,
        )

        # Test
        self.broker._handle_trade = Mock()
        threading.Thread(target=self.broker.process, daemon=True).start()
        self.bus.publish(EventType.TRADE, event)
        sleep(1)

        # Validate
        args = self.broker._handle_trade.call_args[0]
        self.assertEqual(args[0], event)

    def test_update_positions_update(self):
        symbol = self.symbols_map.get_symbol("AAPL")
        contract = symbol.contract

        # Old Position
        old_position = EquityPosition(
            action="BUY",
            avg_price=10,
            quantity=100,
            quantity_multiplier=1,
            price_multiplier=1,
            market_price=20,
        )
        self.broker.positions[contract] = old_position

        # New order
        action = Action.SELL
        quantity = -50
        fill_price = 25

        # Test
        self.broker._update_positions(
            symbol,
            action,
            quantity,
            fill_price,
        )

        # Expected
        full_available_funds_available = 25 * abs(50) + self.capital

        # Validate
        self.assertEqual(
            self.broker.account.full_available_funds,
            full_available_funds_available,
        )

    def test_update_positions_new(self):
        symbol = self.symbols_map.get_symbol("AAPL")

        # New order
        action = Action.SELL
        quantity = -50
        fill_price = 25

        # Test
        self.broker._update_positions(symbol, action, quantity, fill_price)

        # Expected
        full_available_funds_available = (
            fill_price * abs(quantity) + self.capital
        )

        # Validate
        self.assertEqual(
            self.broker.account.full_available_funds,
            full_available_funds_available,
        )

    def test_update_account(self):
        # Position1
        hogs_position = FuturePosition(
            action="BUY",
            avg_price=10,
            quantity=80,
            quantity_multiplier=400000,
            price_multiplier=0.01,
            market_price=10,
            initial_margin=5000,
        )
        hogs_contract = self.symbols_map.get_symbol("HEJ4").contract
        self.broker.positions[hogs_contract] = hogs_position

        # Position2
        aapl_position = EquityPosition(
            action="BUY",
            avg_price=10,
            quantity=100,
            quantity_multiplier=1,
            price_multiplier=1,
            market_price=10,
        )
        aapl_contract = self.symbols_map.get_symbol("AAPL").contract
        self.broker.positions[aapl_contract] = aapl_position

        # Mock orderbook responses
        self.order_book.retrieve = Mock(
            return_value=OhlcvMsg(
                instrument_id=1,
                ts_event=1777700000000000,
                open=int(80.90 * 1e9),
                close=int(90 * 1e9),
                high=int(75.90 * 1e9),
                low=int(8800.09 * 1e9),
                volume=880000,
            )
        )
        self.order_book._last_updated = 1777700000000000
        current_price = 90

        # Test
        self.broker._update_account()

        # Expected
        hogs_unrealized_pnl = (
            (current_price - hogs_position.avg_price)
            * hogs_position.quantity
            * hogs_position.quantity_multiplier
            * hogs_position.price_multiplier
        )
        hogs_liquidation_value = (
            hogs_position.quantity * hogs_position.initial_margin
        ) + hogs_unrealized_pnl
        hogs_margin_required = (
            hogs_position.initial_margin * hogs_position.quantity
        )

        aapl_unrealized_pnl = (
            current_price - aapl_position.avg_price
        ) * aapl_position.quantity
        aapl_liquidation_value = current_price * aapl_position.quantity
        aapl_margin_required = 0

        expected_account = Account(
            timestamp=1777700000000000,
            full_available_funds=self.capital,
            net_liquidation=hogs_liquidation_value
            + aapl_liquidation_value
            + self.capital,
            full_init_margin_req=hogs_margin_required + aapl_margin_required,
            unrealized_pnl=hogs_unrealized_pnl + aapl_unrealized_pnl,
        )

        # Validate
        self.assertEqual(self.broker.account, expected_account)

    def test_update_trades(self):
        timestamp = 1651500000
        trade_id = 1
        leg_id = 2
        ticker = "AAPL"
        symbol = self.symbols_map.get_symbol(ticker)
        quantity = -10
        action = Action.LONG
        fill_price = 9.9
        fees = 90.9

        # Exception
        id = f"{trade_id}{leg_id}{action}"
        expected_trade = Trade(
            timestamp=timestamp,
            trade_id=trade_id,
            leg_id=leg_id,
            instrument=symbol.instrument_id,
            quantity=round(quantity, 4),
            avg_price=fill_price,
            trade_value=round(fill_price * quantity, 2),
            trade_cost=round(abs(quantity) * fill_price, 2),
            action=action.value,
            fees=round(fees, 4),
        )

        # Test
        self.bus.publish = Mock()
        self.broker._update_trades(
            timestamp,
            trade_id,
            leg_id,
            symbol,
            quantity,
            action,
            fill_price,
            fees,
        )

        # Validate
        args = self.bus.publish.call_args[0]
        self.assertEqual(args[0], EventType.TRADE_UPDATE)
        self.assertEqual(args[1], TradeEvent(id, expected_trade))

    def test_mark_to_market(self):
        self.broker._update_account = Mock()

        # Test
        self.logger.logger.info = Mock()
        self.broker.mark_to_market()

        # Validate
        self.broker._update_account.assert_called()

    def test_check_margin_call(self):
        # Margin Call
        self.broker.account.full_available_funds = 100
        self.broker.account.full_init_margin_req = 2000

        # Test
        self.logger.logger.info = Mock()
        self.broker.check_margin_call()

        # Validate
        self.logger.logger.info.assert_called_with("Margin call triggered.")

    def test_check_margin_call_no_call(self):
        # No Margin Call
        self.broker.account.full_available_funds = 2000
        self.broker.account.full_init_margin_req = 200

        # Test
        self.logger.logger.info = Mock()
        self.broker.check_margin_call()

        # Validate
        self.logger.logger.info.assert_not_called()

    def test_liquidate_positions(self):
        self.bus.publish = Mock()

        # Position1
        hogs_position = FuturePosition(
            action="BUY",
            avg_price=10,
            quantity=80,
            quantity_multiplier=40000,
            price_multiplier=0.01,
            market_price=10,
            initial_margin=4564.17,
        )
        hogs_contract = self.symbols_map.get_symbol("HEJ4").contract
        self.broker.positions[hogs_contract] = hogs_position

        hogs_trade = Trade(
            timestamp=165000000,
            trade_id=1,
            leg_id=1,
            instrument=self.hogs.instrument_id,
            quantity=round(hogs_position.quantity, 4),
            avg_price=hogs_position.avg_price,
            trade_value=round(
                hogs_position.avg_price
                * hogs_position.price_multiplier
                * hogs_position.quantity_multiplier
                * hogs_position.quantity,
                2,
            ),
            trade_cost=hogs_position.initial_margin * hogs_position.quantity,
            action=hogs_position.action,
            fees=70,
        )
        self.broker.last_trades[hogs_contract] = hogs_trade

        # Position2
        aapl_position = EquityPosition(
            action="BUY",
            avg_price=10,
            quantity=100,
            quantity_multiplier=1,
            price_multiplier=1,
            market_price=10,
        )
        aapl_contract = self.symbols_map.get_symbol("AAPL").contract
        self.broker.positions[aapl_contract] = aapl_position

        aapl_trade = Trade(
            timestamp=165000000,
            trade_id=2,
            leg_id=2,
            instrument=self.aapl.instrument_id,
            quantity=round(aapl_position.quantity, 4),
            avg_price=aapl_position.avg_price,
            trade_value=round(
                aapl_position.avg_price * aapl_position.quantity, 2
            ),
            trade_cost=round(
                aapl_position.avg_price * aapl_position.quantity, 2
            ),
            action=aapl_position.action,
            fees=70,
        )
        self.broker.last_trades[aapl_contract] = aapl_trade

        # Mock order book response
        self.order_book.retrieve = Mock(
            return_value=OhlcvMsg(
                instrument_id=1,
                ts_event=1777700000000000,
                open=int(80.90 * 1e9),
                close=int(90 * 1e9),
                high=int(75.90 * 1e9),
                low=int(8800.09 * 1e9),
                volume=880000,
            )
        )
        self.order_book._last_updated = 17777000000000
        current_price = 90

        # Test
        self.broker.liquidate_positions()

        # Expected
        hogs_trade_liquidated = Trade(
            timestamp=17777000000000,
            trade_id=1,
            leg_id=1,
            instrument=self.hogs.instrument_id,
            quantity=round(hogs_position.quantity * -1, 4),
            avg_price=current_price * hogs_position.price_multiplier,
            trade_value=round(
                (
                    current_price
                    * hogs_position.quantity
                    * hogs_position.quantity_multiplier
                    * hogs_position.price_multiplier
                ),
                2,
            ),
            trade_cost=hogs_position.initial_margin * hogs_position.quantity,
            action=Action.SELL.value,
            fees=0.0,
        )
        id = f"{1}{1}{hogs_trade_liquidated.action}"
        trade1 = TradeEvent(id, hogs_trade_liquidated)

        aapl_trade_liquidated = Trade(
            timestamp=17777000000000,
            trade_id=2,
            leg_id=2,
            instrument=self.aapl.instrument_id,
            quantity=round(aapl_position.quantity * -1, 4),
            avg_price=current_price * 1,
            trade_value=round(current_price * aapl_position.quantity, 2),
            trade_cost=round(current_price * abs(aapl_position.quantity), 2),
            action=Action.SELL.value,
            fees=0.0,
        )
        id2 = f"{2}{2}{aapl_trade_liquidated.action}"
        trade2 = TradeEvent(id2, aapl_trade_liquidated)

        # Validate
        self.assertEqual(self.bus.publish.call_count, 2)

        # Access all calls made to publish
        calls = self.bus.publish.call_args_list

        # Validate the first call
        first_call_args = calls[0][0]
        self.assertEqual(first_call_args[0], EventType.TRADE_UPDATE)
        self.assertEqual(first_call_args[1], trade1)

        # Validate the second call
        second_call_args = calls[1][0]
        # Replace with your expected arguments for the second call
        self.assertEqual(second_call_args[0], EventType.TRADE_UPDATE)
        self.assertEqual(second_call_args[1], trade2)

    def test_return_positions_quantity_not_zero(self):
        # Variables
        ticker = "HEJ4"
        symbol = self.symbols_map.get_symbol(ticker)
        id = self.symbols_map.get_id(ticker)

        position = EquityPosition(
            action="SELL",
            quantity=-10,
            avg_price=100,
            quantity_multiplier=symbol.quantity_multiplier,
            price_multiplier=symbol.price_multiplier,
            market_price=10,
        )
        self.broker.positions[symbol.contract] = position

        # Test
        self.bus.publish = Mock()
        self.broker.return_positions()

        # Valdiate
        args = self.bus.publish.call_args[0]
        self.assertEqual(args[0], EventType.POSITION_UPDATE)
        self.assertEqual(args[1], (id, position))

    def test_return_positions_quantity_zero(self):
        # Variables
        ticker = "HEJ4"
        symbol = self.symbols_map.get_symbol(ticker)
        id = self.symbols_map.get_id(ticker)

        position = EquityPosition(
            action="SELL",
            quantity=0,
            avg_price=100,
            quantity_multiplier=symbol.quantity_multiplier,
            price_multiplier=symbol.price_multiplier,
            market_price=10,
        )

        self.broker.positions[symbol.contract] = position

        # Test
        self.bus.publish = Mock()
        self.broker.return_positions()

        # Valdiate
        args = self.bus.publish.call_args[0]
        self.assertEqual(args[0], EventType.POSITION_UPDATE)
        self.assertEqual(args[1], (id, position))
        self.assertEqual(self.broker.positions, {})


if __name__ == "__main__":
    unittest.main()

    # def test_place_order(self):
    #     # Mock order data
    #     timestamp = 1655000000
    #     trade_id = 1
    #     leg_id = 1
    #     action = Action.LONG
    #     contract = self.hogs.contract
    #
    #     bar = OhlcvMsg(
    #         instrument_id=1,
    #         ts_event=1707221160000000000,
    #         open=int(80.90 * 1e9),
    #         close=int(9000.90 * 1e9),
    #         high=int(75.90 * 1e9),
    #         low=int(8800.09 * 1e9),
    #         volume=880000,
    #     )
    #
    #     # Mock methods
    #     self.order_book.retrieve.return_value = bar
    #     self.hogs.commission_fees = Mock(return_value=10)
    #     self.hogs.slippage_price = Mock(return_value=9)
    #     order = MarketOrder(action, quantity=10)
    #
    #     # Test
    #     self.dummy_broker._update_positions = Mock()
    #     self.dummy_broker._update_account = Mock()
    #     self.dummy_broker._update_trades = Mock()
    #     self.dummy_broker._set_execution = Mock()
    #     self.dummy_broker.placeOrder(
    #         timestamp,
    #         trade_id,
    #         leg_id,
    #         action,
    #         contract,
    #         order,
    #     )
    #
    #     # Validate
    #     self.assertTrue(self.dummy_broker._update_positions.called)
    #     self.assertTrue(self.dummy_broker._update_account.called)
    #     self.assertTrue(self.dummy_broker._update_trades.called)
    #     self.assertTrue(self.dummy_broker._set_execution.called)

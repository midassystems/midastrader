import unittest
from datetime import datetime, time

from midastrader.structs.events import OrderEvent
from midastrader.structs.orders import Action, MarketOrder
from midastrader.structs.symbol import (
    Equity,
    Currency,
    Venue,
    Industry,
    SecurityType,
    TradingSession,
)


class TestOrderEvent(unittest.TestCase):
    def setUp(self) -> None:
        # Test data
        self.timestamp = 1651500000
        self.action = Action.LONG
        self.trade_id = 2
        self.signal_id = 2
        self.order = MarketOrder(self.signal_id, self.action, 10)
        self.symbol = Equity(
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

    # Basic Validation
    def test_basic_validation(self):
        # Test
        event = OrderEvent(
            timestamp=self.timestamp,
            signal_id=self.signal_id,
            action=self.action,
            order=self.order,
            symbol=self.symbol,
        )
        # Validate
        self.assertEqual(event.timestamp, self.timestamp)
        self.assertEqual(event.order, self.order)
        self.assertEqual(event.symbol, self.symbol)
        self.assertEqual(event.action, self.action)
        self.assertEqual(event.signal_id, self.signal_id)

    # Type Checks
    def test_type_constraint(self):
        with self.assertRaisesRegex(
            TypeError, "'timestamp' must be of type int."
        ):
            OrderEvent(
                timestamp=datetime(2024, 1, 1),  # pyright: ignore
                signal_id=self.signal_id,
                action=self.action,
                order=self.order,
                symbol=self.symbol,
            )

        with self.assertRaisesRegex(
            TypeError, "'signal_id' must be of type int."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                signal_id="1",  # pyright: ignore
                action=self.action,
                order=self.order,
                symbol=self.symbol,
            )

        with self.assertRaisesRegex(
            TypeError, "'action' must be of type Action enum."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                signal_id=self.signal_id,
                action=123,  # pyright: ignore
                order=self.order,
                symbol=self.symbol,
            )

        with self.assertRaisesRegex(
            TypeError, "'symbol' must be of type Symbol."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                signal_id=self.signal_id,
                action=self.action,
                order=self.order,
                symbol="",  # pyright: ignore
            )

        with self.assertRaisesRegex(
            TypeError, "'order' must be of type BaseOrder."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                signal_id=self.signal_id,
                action=self.action,
                order="self.order",  # pyright: ignore
                symbol=self.symbol,
            )

    # Constraint Check
    def test_value_constraint(self):
        with self.assertRaisesRegex(
            ValueError, "'signal_id' must be greater than zero."
        ):
            OrderEvent(
                timestamp=self.timestamp,
                signal_id=0,
                action=self.action,
                order=self.order,
                symbol=self.symbol,
            )


if __name__ == "__main__":
    unittest.main()

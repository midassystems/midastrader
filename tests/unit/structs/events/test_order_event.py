from typing import List
import unittest
from datetime import datetime, time

from midastrader.structs.events import OrderEvent
from midastrader.structs.orders import Action, BaseOrder, MarketOrder
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
        self.orders: List[BaseOrder] = [
            MarketOrder(1, self.signal_id, self.action, 10)
        ]
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
            maintenance_margin=0,
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
        event = OrderEvent(self.timestamp, self.orders)

        # Validate
        self.assertEqual(event.timestamp, self.timestamp)
        self.assertEqual(event.orders, self.orders)

    # Type Checks
    def test_type_constraint(self):
        with self.assertRaisesRegex(
            TypeError, "'timestamp' must be of type int."
        ):
            OrderEvent(
                datetime(2024, 1, 1),  # pyright: ignore
                self.orders,
            )

        with self.assertRaises(TypeError):
            OrderEvent(
                self.timestamp,
                ["self.order"],  # pyright: ignore
            )

        with self.assertRaises(TypeError):
            OrderEvent(
                self.timestamp,
                "self.order",  # pyright: ignore
            )


if __name__ == "__main__":
    unittest.main()

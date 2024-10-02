import unittest
import numpy as np
from unittest.mock import Mock
from midas.account import Account
from midas.positions import EquityPosition
from midas.active_orders import ActiveOrder
from midas.engine.components.observer.database_updater import (
    DatabaseUpdater,
)
from midas.engine.components.observer.base import Subject, EventType


class ChildSubject(Subject):
    def __init__(self):
        super().__init__()
        self.positions = {
            "HE": EquityPosition(
                action="BUY",
                avg_price=10.90,
                quantity=100,
                quantity_multiplier=1,
                price_multiplier=1,
                market_price=12,
            )
        }

        self.order = {
            123: ActiveOrder(
                permId=10,
                parentId=1,
                clientId=1,
                orderId=123,
                account="dwdfwf3e2",
                instrument=123,
                secType="FUT",
                exchange="CME",
                action="BUY",
                orderType="MKT",
                totalQty=10,
                cashQty=10000,
                lmtPrice=0.0,
                auxPrice=0.0,
                status="PreSubmitted",
            )
        }

        self.account = Account(
            timestamp=167700000000000,
            full_available_funds=100000.0,
            full_init_margin_req=100000.0,
            net_liquidation=100000.0,
            unrealized_pnl=100000.0,
            full_maint_margin_req=100000.0,
            currency="USD",
        )

        self.market_event = 4
        self.risk = 5

    @property
    def get_positions(self):
        return self.positions

    @property
    def get_account(self):
        return self.account

    @property
    def get_active_orders(self):
        return self.order

    def current_prices(self):
        return self.market_event


class TestDatabaseUpdater(unittest.TestCase):
    def setUp(self) -> None:
        # Mock database
        self.database_client = Mock()

        # Instantiate database handle_eventr
        self.session_id = 12345
        self.observer = DatabaseUpdater(
            self.database_client, session_id=self.session_id
        )

        # Observer pattern
        self.subject = ChildSubject()
        self.subject.attach(self.observer, EventType.MARKET_DATA)
        self.subject.attach(self.observer, EventType.ORDER_UPDATE)
        self.subject.attach(self.observer, EventType.POSITION_UPDATE)
        self.subject.attach(self.observer, EventType.ACCOUNT_UPDATE)
        self.subject.attach(self.observer, EventType.RISK_UPDATE)

    # Basic validation
    def test_handle_event_position(self):
        # Test
        self.observer.handle_event(self.subject, EventType.POSITION_UPDATE)

        # Validation
        self.database_client.handle_event_positions.assert_called_once

    def test_create_position(self):
        self.database_client.handle_event_positions.side_effect = ValueError(
            "Not found"
        )

        # Test
        self.observer.handle_event(self.subject, EventType.POSITION_UPDATE)

        # Validation
        self.database_client.create_positions.assert_called_once

    def test_handle_event_account(self):
        # Test
        self.observer.handle_event(self.subject, EventType.ACCOUNT_UPDATE)

        # Validation
        self.database_client.handle_event_account.assert_called_once

    def test_create_account(self):
        self.database_client.handle_event_account.side_effect = ValueError(
            "Not found"
        )

        # Test
        self.observer.handle_event(self.subject, EventType.ACCOUNT_UPDATE)

        # Validation
        self.database_client.create_account.assert_called_once

    def test_handle_event_order(self):
        # Test
        self.observer.handle_event(self.subject, EventType.ORDER_UPDATE)

        # Validation
        self.database_client.handle_event_order.assert_called_once

    def test_create_order(self):
        self.database_client.handle_event_order.side_effect = ValueError(
            "Not found"
        )

        # Test
        self.observer.handle_event(self.subject, EventType.MARKET_DATA)

        # Validation
        self.database_client.create_order.assert_called_once

    def test_handle_event_risk(self):
        pass

    def test_handle_event_market_data(self):
        pass

    # Type Validation
    def test_handle_event_type_invalid(self):
        with self.assertRaisesRegex(
            TypeError, "'event_type' field must be of instance EventType enum."
        ):
            self.observer.handle_event(self.subject, "invalid")


if __name__ == "__main__":
    unittest.main()

import unittest
from midas.engine.components.observer.base import EventType, Observer, Subject


class Child(Observer):
    def handle_event(self, subject, event_type: EventType):
        if event_type == EventType.POSITION_UPDATE:
            return 1
        elif event_type == EventType.ORDER_UPDATE:
            return 2
        elif event_type == EventType.ACCOUNT_UPDATE:
            return 3
        elif event_type == EventType.MARKET_DATA:
            return 4
        elif event_type == EventType.RISK_UPDATE:
            return 5


class TestObserver(unittest.TestCase):
    def setUp(self) -> None:
        # Test observer child
        self.child_observer = Child()

    def test_inheritance(self):
        # Test
        positon_event = self.child_observer.handle_event(
            None, EventType.POSITION_UPDATE
        )
        order_event = self.child_observer.handle_event(
            None, EventType.ORDER_UPDATE
        )
        account_event = self.child_observer.handle_event(
            None, EventType.ACCOUNT_UPDATE
        )
        market_event = self.child_observer.handle_event(
            None, EventType.MARKET_DATA
        )
        risk_event = self.child_observer.handle_event(
            None, EventType.RISK_UPDATE
        )

        # Expected
        excepted_position_return = 1
        excepted_order_return = 2
        excepted_account_return = 3
        excepted_market_return = 4
        excepted_risk_return = 5

        # Validation
        self.assertEqual(positon_event, excepted_position_return)
        self.assertEqual(order_event, excepted_order_return)
        self.assertEqual(account_event, excepted_account_return)
        self.assertEqual(market_event, excepted_market_return)
        self.assertEqual(risk_event, excepted_risk_return)


class ChildObserver(Observer):
    def __init__(self) -> None:
        self.tester = None

    def handle_event(self, subject, event_type: EventType):
        if event_type == EventType.POSITION_UPDATE:
            self.tester = 1
        elif event_type == EventType.ORDER_UPDATE:
            self.tester = 2
        elif event_type == EventType.ACCOUNT_UPDATE:
            self.tester = 3
        elif event_type == EventType.MARKET_DATA:
            self.tester = 4
        elif event_type == EventType.RISK_UPDATE:
            self.tester = 5


class ChildSubject(Subject):
    def __init__(self):
        super().__init__()


class TestSubject(unittest.TestCase):
    def setUp(self) -> None:
        # Test subject and observer
        self.subject = ChildSubject()
        self.observer = ChildObserver()

    def test_attach(self):
        # Test
        self.subject.attach(self.observer, EventType.MARKET_DATA)

        # Expected
        expected_observers = {EventType.MARKET_DATA: [self.observer]}

        # Validate
        self.assertEqual(self.subject._observers, expected_observers)

        # Test2
        self.subject.attach(self.observer, EventType.ACCOUNT_UPDATE)

        # Expected
        expected_observers2 = {
            EventType.MARKET_DATA: [self.observer],
            EventType.ACCOUNT_UPDATE: [self.observer],
        }

        # Validate
        self.assertEqual(self.subject._observers, expected_observers2)

    def test_detach(self):
        # Set-up
        self.subject.attach(self.observer, EventType.MARKET_DATA)
        self.subject.attach(self.observer, EventType.ACCOUNT_UPDATE)
        observers = {
            EventType.MARKET_DATA: [self.observer],
            EventType.ACCOUNT_UPDATE: [self.observer],
        }
        self.assertEqual(self.subject._observers, observers)

        # Test
        self.subject.detach(self.observer, EventType.MARKET_DATA)
        self.subject.detach(self.observer, EventType.ACCOUNT_UPDATE)

        # Validate
        self.assertEqual(
            self.subject._observers,
            {EventType.MARKET_DATA: [], EventType.ACCOUNT_UPDATE: []},
        )

    def test_notify(self):
        # Set-up
        self.subject.attach(self.observer, EventType.MARKET_DATA)
        self.subject.attach(self.observer, EventType.ACCOUNT_UPDATE)
        _ = {
            EventType.MARKET_DATA: [self.observer],
            EventType.ACCOUNT_UPDATE: [self.observer],
        }

        # Test1
        self.subject.notify(EventType.MARKET_DATA)
        self.assertEqual(self.observer.tester, 4)

        # Test2
        self.subject.notify(EventType.ACCOUNT_UPDATE)
        self.assertEqual(self.observer.tester, 3)


if __name__ == "__main__":
    unittest.main()

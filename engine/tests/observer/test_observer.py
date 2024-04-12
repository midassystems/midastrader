import unittest
from engine.observer import EventType, Observer,  Subject

class TestObserver(unittest.TestCase):
    def setUp(self) -> None:
        class Child(Observer):
            def update(self, subject, event_type: EventType):
                if event_type == EventType.POSITION_UPDATE:
                    return 1
                elif event_type == EventType.ORDER_UPDATE:
                    return 2
                elif event_type == EventType.ACCOUNT_DETAIL_UPDATE:
                    return 3
                elif event_type == EventType.MARKET_EVENT:
                    return 4
                elif event_type == EventType.RISK_MODEL_UPDATE:
                    return 5
        
        self.child_observer = Child()
    
    def test_inheritance(self):
        # Expected 
        excepted_position_return = 1
        excepted_order_return = 2
        excepted_account_return = 3
        excepted_market_return = 4
        excepted_risk_return = 5

        # Test
        positon_event = self.child_observer.update(None,EventType.POSITION_UPDATE)
        order_event = self.child_observer.update(None,EventType.ORDER_UPDATE)
        account_event = self.child_observer.update(None,EventType.ACCOUNT_DETAIL_UPDATE)
        market_event = self.child_observer.update(None,EventType.MARKET_EVENT)
        risk_event = self.child_observer.update(None,EventType.RISK_MODEL_UPDATE)

        # Validation
        self.assertEqual(positon_event, excepted_position_return)
        self.assertEqual(order_event, excepted_order_return)
        self.assertEqual(account_event, excepted_account_return)
        self.assertEqual(market_event, excepted_market_return)
        self.assertEqual(risk_event, excepted_risk_return)

class TestSubject(unittest.TestCase):
    def setUp(self) -> None:
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
    
        class ChildSubject(Subject):
            def __init__(self):
                super().__init__()

        self.subject = ChildSubject()
        self.observer = ChildObserver()

    def test_attach(self):
        # expected
        expected_observers = {EventType.MARKET_EVENT : [self.observer]}
        expected_observers2 = {EventType.MARKET_EVENT : [self.observer], EventType.ACCOUNT_DETAIL_UPDATE : [self.observer]}
        
        # Test1
        self.subject.attach(self.observer, EventType.MARKET_EVENT)

        # Validate
        self.assertEqual(self.subject._observers, expected_observers)

        # Test2
        self.subject.attach(self.observer, EventType.ACCOUNT_DETAIL_UPDATE)

        # Vlaidate
        self.assertEqual(self.subject._observers, expected_observers2)

    def test_detach(self):
        # Set up
        self.subject.attach(self.observer, EventType.MARKET_EVENT)
        self.subject.attach(self.observer, EventType.ACCOUNT_DETAIL_UPDATE)
        observers = {EventType.MARKET_EVENT : [self.observer], EventType.ACCOUNT_DETAIL_UPDATE : [self.observer]}
        self.assertEqual(self.subject._observers, observers)

        # Test
        self.subject.detach(self.observer, EventType.MARKET_EVENT)
        self.subject.detach(self.observer, EventType.ACCOUNT_DETAIL_UPDATE)

        # Validate
        self.assertEqual(self.subject._observers, {EventType.MARKET_EVENT : [], EventType.ACCOUNT_DETAIL_UPDATE : []})

    def test_notify(self):
        # Set up
        self.subject.attach(self.observer, EventType.MARKET_EVENT)
        self.subject.attach(self.observer, EventType.ACCOUNT_DETAIL_UPDATE)
        observers = {EventType.MARKET_EVENT : [self.observer], EventType.ACCOUNT_DETAIL_UPDATE : [self.observer]}

        # Test
        self.subject.notify(EventType.MARKET_EVENT)
        self.assertEqual(self.observer.tester, 4)

        self.subject.notify(EventType.ACCOUNT_DETAIL_UPDATE)
        self.assertEqual(self.observer.tester, 3)


if __name__ == "__main__":
    unittest.main()
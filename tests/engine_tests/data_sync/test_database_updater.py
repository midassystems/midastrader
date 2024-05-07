import unittest
from unittest.mock import Mock

from midas.engine.data_sync import DatabaseUpdater
from midas.engine.observer import Subject,EventType

from midas.shared.portfolio import Position, ActiveOrder, AccountDetails


class ChildSubject(Subject):
    def __init__(self):
        super().__init__()
        self.positions =  { "HE": Position(action='BUY', 
                            avg_cost=10.9,
                            quantity=100,
                            total_cost=100000,
                            market_value=10000,
                            quantity_multiplier=40000,
                            price_multiplier=0.01,
                            initial_margin=0)}
        
        self.order = { 123: ActiveOrder(permId = 10,
                                    clientId= 1, 
                                    orderId= 123, 
                                    account= "dwdfwf3e2", 
                                    symbol= "HE", 
                                    secType= "FUT",
                                    exchange= "CME", 
                                    action= "BUY", 
                                    orderType= "MKT",
                                    totalQty= 10, 
                                    cashQty= 10000, 
                                    lmtPrice= 0.0, 
                                    auxPrice= 0.0, 
                                    status= "PreSubmitted")}
        
        self.account = AccountDetails(FullAvailableFunds = 100000.0, 
                                        FullInitMarginReq =  100000.0,
                                        NetLiquidation = 100000.0,
                                        UnrealizedPnL =  100000.0,
                                        FullMaintMarginReq =  100000.0,
                                        Currency = 'USD')
        
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
        self.database_client = Mock()
        self.session_id = 12345
        self.observer = DatabaseUpdater(self.database_client, session_id=self.session_id)

        # Observer pattern
        self.subject = ChildSubject()
        self.subject.attach(self.observer, EventType.MARKET_EVENT)
        self.subject.attach(self.observer, EventType.ORDER_UPDATE)
        self.subject.attach(self.observer, EventType.POSITION_UPDATE)
        self.subject.attach(self.observer, EventType.ACCOUNT_DETAIL_UPDATE)
        self.subject.attach(self.observer, EventType.RISK_MODEL_UPDATE)
    
    # Basic validation
    def test_update_position(self):
        # test
        self.observer.update(self.subject, EventType.POSITION_UPDATE)

        # validation
        self.database_client.update_positions.assert_called_once

    def test_create_position(self):
        self.database_client.update_positions.side_effect = ValueError("Not found")
        # test
        self.observer.update(self.subject, EventType.POSITION_UPDATE)

        # validation
        self.database_client.create_positions.assert_called_once

    def test_update_account(self):
        # test
        self.observer.update(self.subject, EventType.ACCOUNT_DETAIL_UPDATE)

        # validation
        self.database_client.update_account.assert_called_once
        
    def test_create_account(self):
        self.database_client.update_account.side_effect = ValueError("Not found")
        # test
        self.observer.update(self.subject, EventType.ACCOUNT_DETAIL_UPDATE)

        # validation
        self.database_client.create_account.assert_called_once

    def test_update_order(self):
        # test
        self.observer.update(self.subject, EventType.ORDER_UPDATE)

        # validation
        self.database_client.update_order.assert_called_once

    def test_create_order(self):
        self.database_client.update_order.side_effect = ValueError("Not found")
        # test
        self.observer.update(self.subject, EventType.MARKET_EVENT)

        # validation
        self.database_client.create_order.assert_called_once

    def test_update_risk(self):
        pass

    def test_update_market_data(self):
        pass
    
    # Type Validation
    def test_update_type_invalid(self):
        with self.assertRaisesRegex(TypeError, "event_type must be of instance EventType enum."):
            self.observer.update(self.subject, "invalid")


if __name__ == "__main__":
    unittest.main()
    

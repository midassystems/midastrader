from enum import Enum, auto
from midas_database import DatabaseClient
from midas.observer import Observer, EventType


class DatabaseUpdater(Observer):
    def __init__(self, database_client: DatabaseClient, session_id:int):
        self.database_client = database_client
        self.session_id = session_id

        self.database_client.create_session(self.session_id)
    
    def update(self, subject, event_type: EventType):
        if not isinstance(event_type, EventType):
            raise TypeError(f"event_type must be of instance EventType enum.")
        
        if event_type == EventType.POSITION_UPDATE:
            positions = subject.get_positions
            data = {"data": {ticker: position.to_dict() for ticker, position in positions.items()}}
            self._update_positions(data)
        elif event_type == EventType.ORDER_UPDATE:
            data = {"data" : subject.get_active_orders}
            self._update_orders(data)
        elif event_type == EventType.ACCOUNT_DETAIL_UPDATE:
            data = {"data" :subject.get_account}
            self._update_account(data)
        # elif event_type == EventType.MARKET_EVENT:
        #     data = subject.current_prices()
        # elif event_type == EventType.RISK_MODEL_UPDATE:
        #     data = subject.get_latest_market_data()

    def _update_positions(self, data:dict):
        try:
            self.database_client.update_positions(self.session_id, data)
        except ValueError as e:
            if "Not found" in str(e):
                try:
                    self.database_client.create_positions(self.session_id, data)
                except ValueError as e:
                        raise e
            else:
                raise e
            
    def _update_orders(self, data: dict):
        try:
            self.database_client.update_orders(self.session_id, data)
        except ValueError as e:
            if "Not found" in str(e):
                try:
                    self.database_client.create_orders(self.session_id, data)
                except ValueError as e:
                        raise e
            else:
                raise e

    def _update_account(self, data: dict):
        try:
            self.database_client.update_account(self.session_id, data)
        except ValueError as e:
            if "Not found" in str(e):
                try:
                    self.database_client.create_account(self.session_id, data)
                except ValueError as e:
                        raise e
            else:
                raise e

    def delete_session(self):
        self.database_client.delete_session(self.session_id)

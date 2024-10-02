from midasClient.client import DatabaseClient
from midas.engine.components.observer import Observer, EventType


class DatabaseUpdater(Observer):
    """
    Observes trading events and updates the database based on these events.

    As an observer, this class listens to various events within the trading system such as updates to positions,
    orders, and account details. It is responsible for ensuring that all relevant changes in the trading system
    are reflected in the database, thereby maintaining data integrity and consistency.

    Attributes:
    - database_client (DatabaseClient): The client responsible for database operations.
    - session_id (int): The unique identifier for the current trading session.
    """

    def __init__(self, database_client: DatabaseClient, session_id: int):
        """
        Initializes the DatabaseUpdater with a specific database client and session ID.

        Upon initialization, it also creates a new session in the database to store data relevant to the current trading activities.

        Parameters:
        - database_client (DatabaseClient): The client to perform database operations.
        - session_id (int): The ID used to identify the session in the database.
        """
        self.database_client = database_client
        self.session_id = session_id

        # Create trading session
        self.database_client.create_session(self.session_id)

    def handle_event(self, subject, event_type: EventType):
        """
        Responds to events by updating the database based on the event type.

        Depending on the event type, it extracts data from the subject (usually the trading system component
        firing the event) and calls the appropriate method to update or create records in the database.

        Parameters:
        - subject (varies): The object that triggered the event.
        - event_type (EventType): The type of event that was triggered.
        """
        if not isinstance(event_type, EventType):
            raise TypeError(
                "'event_type' field must be of instance EventType enum."
            )

        if event_type == EventType.POSITION_UPDATE:
            positions = subject.get_positions
            data = {
                "data": {
                    ticker: position.to_dict()
                    for ticker, position in positions.items()
                }
            }
            self._update_positions(data)
        elif event_type == EventType.ORDER_UPDATE:
            orders = subject.get_active_orders
            data = {
                "data": {id: order.to_dict() for id, order in orders.items()}
            }
            # data = {"data": subject.get_active_orders.to_dict()}
            self._update_orders(data)
        elif event_type == EventType.ACCOUNT_UPDATE:
            account = subject.get_account
            data = {"data": account.to_dict()}
            self._update_account(data)
        # elif event_type == EventType.MARKET_EVENT:
        #     data = subject.current_prices()
        # elif event_type == EventType.RISK_MODEL_UPDATE:
        #     data = subject.get_latest_market_data()

    def _update_positions(self, data: dict):
        """
        Attempts to update position records in the database; creates them if they don't exist.

        Parameters:
        - data (dict): The data to be updated or created in the database.
        """
        try:
            self.database_client.update_positions(self.session_id, data)
        except ValueError as e:
            if "Not found" in str(e):
                try:
                    self.database_client.create_positions(
                        self.session_id, data
                    )
                except ValueError as e:
                    raise e
            else:
                raise e

    def _update_orders(self, data: dict):
        """
        Attempts to update order records in the database; creates them if they don't exist.

        Parameters:
        - data (dict): The data to be updated or created in the database.
        """
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
        """
        Attempts to update account details in the database; creates them if they don't exist.

        Parameters:
            data (dict): The data to be updated or created in the database.
        """
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
        """
        Deletes all records related to the current session from the database.

        This method is typically called at the end of a trading session to clean up any session-specific data.
        """
        self.database_client.delete_session(self.session_id)

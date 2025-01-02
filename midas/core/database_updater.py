# from midasClient.client import DatabaseClient
#
# # from midas.core_engine.components.observer import Observer, Subject, EventType
#
#
# class DatabaseUpdater(Observer):
#     """
#     Observes trading events and updates the database based on these events.
#
#     This class listens to various events within the trading system, such as updates to positions,
#     orders, and account details. It ensures that all relevant changes in the trading system are
#     reflected in the database, maintaining data integrity and consistency.
#
#     Attributes:
#         database_client (DatabaseClient): The client responsible for database operations.
#         session_id (int): The unique identifier for the current trading session.
#     """
#
#     def __init__(self, database_client: DatabaseClient, session_id: int):
#         """
#         Initializes the DatabaseUpdater with a specific database client and session ID.
#
#         Upon initialization, it also creates a new session in the database to store data
#         relevant to the current trading activities.
#
#         Behavior:
#             - A new session is created in the database using the provided `session_id`.
#
#         Args:
#             database_client (DatabaseClient): The client to perform database operations.
#             session_id (int): The ID used to identify the session in the database.
#
#         """
#         self.database_client = database_client
#         self.session_id = session_id
#         self.database_client.create_session(self.session_id)
#
#     def handle_event(self, subject: Subject, event_type: EventType) -> None:
#         """
#         Responds to events by updating the database based on the event type.
#
#         Depending on the event type, it extracts data from the subject (usually the trading system component
#         firing the event) and calls the appropriate method to update or create records in the database.
#
#         Behavior:
#             - For `POSITION_UPDATE`, updates position records in the database.
#             - For `ORDER_UPDATE`, updates active order records in the database.
#             - For `ACCOUNT_UPDATE`, updates account details in the database.
#
#         Args:
#             subject (Subject): The object that triggered the event.
#             event_type (EventType): The type of event that was triggered.
#
#         Raises:
#             TypeError: If `event_type` is not an instance of `EventType`.
#         """
#         if not isinstance(event_type, EventType):
#             raise TypeError(
#                 "'event_type' field must be of instance EventType enum."
#             )
#
#         if event_type == EventType.POSITION_UPDATE:
#             positions = subject.get_positions
#             data = {
#                 "data": {
#                     ticker: position.to_dict()
#                     for ticker, position in positions.items()
#                 }
#             }
#             self._update_positions(data)
#         elif event_type == EventType.ORDER_UPDATE:
#             orders = subject.get_active_orders
#             data = {
#                 "data": {id: order.to_dict() for id, order in orders.items()}
#             }
#             # data = {"data": subject.get_active_orders.to_dict()}
#             self._update_orders(data)
#         elif event_type == EventType.ACCOUNT_UPDATE:
#             account = subject.get_account
#             data = {"data": account.to_dict()}
#             self._update_account(data)
#         # elif event_type == EventType.MARKET_EVENT:
#         #     data = subject.current_prices()
#         # elif event_type == EventType.RISK_MODEL_UPDATE:
#         #     data = subject.get_latest_market_data()
#
#     def _update_positions(self, data: dict) -> None:
#         """
#         Updates or creates position records in the database.
#
#         Args:
#             data (dict): The data to be updated or created in the database.
#
#         Raises:
#             ValueError: If the database operation fails for any reason.
#         """
#         try:
#             self.database_client.update_positions(self.session_id, data)
#         except ValueError as e:
#             if "Not found" in str(e):
#                 try:
#                     self.database_client.create_positions(
#                         self.session_id, data
#                     )
#                 except ValueError as e:
#                     raise e
#             else:
#                 raise e
#
#     def _update_orders(self, data: dict) -> None:
#         """
#         Updates or creates order records in the database.
#
#         Args:
#             data (dict): The data to be updated or created in the database.
#
#         Raises:
#             ValueError: If the database operation fails for any reason.
#         """
#         try:
#             self.database_client.update_orders(self.session_id, data)
#         except ValueError as e:
#             if "Not found" in str(e):
#                 try:
#                     self.database_client.create_orders(self.session_id, data)
#                 except ValueError as e:
#                     raise e
#             else:
#                 raise e
#
#     def _update_account(self, data: dict) -> None:
#         """
#         Updates or creates account details in the database.
#
#         Args:
#             data (dict): The data to be updated or created in the database.
#
#         Raises:
#             ValueError: If the database operation fails for any reason.
#         """
#         try:
#             self.database_client.update_account(self.session_id, data)
#         except ValueError as e:
#             if "Not found" in str(e):
#                 try:
#                     self.database_client.create_account(self.session_id, data)
#                 except ValueError as e:
#                     raise e
#             else:
#                 raise e
#
#     def delete_session(self) -> None:
#         """
#         Deletes all records related to the current session from the database.
#
#         This method is typically called at the end of a trading session to clean up any session-specific data.
#
#         Behavior:
#             - Invokes the `delete_session` method of the database client to remove session-specific records.
#         """
#         self.database_client.delete_session(self.session_id)

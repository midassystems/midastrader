# client.py
import threading
from midas.engine.events import OrderEvent
from midas.account import Account
from midas.engine.components.gateways.base import BaseBrokerClient
from midas.utils.logger import SystemLogger
from midas.engine.config import Config
from midas.symbol import SymbolMap
from midas.engine.components.observer.base import Subject, EventType
from midas.engine.components.gateways.live.broker_client.wrapper import (
    BrokerApp,
)


class BrokerClient(BaseBrokerClient):
    """
    A client for interacting with a broker's API, specifically for broker data feeds (e.g., account, orders, portfolio, trades).

    Attributes:
        logger (logging.Logger): An instance of Logger for logging messages.
        portfolio_server (PortfolioServer): An instance of PortfolioServer for managing portfolio data.
        performance_manager (BasePerformanceManager): An instance of PerformanceManager for managing performance calculations.
        host (str): The host address for connecting to the broker's API.
        port (int): The port number for connecting to the broker's API.
        clientId (str): The client ID used for identifying the client when connecting to the broker's API.
        ib_account (str): The IB account used for managing accounts and positions.
        lock (threading.Lock): A lock for managing thread safety.
    """

    def __init__(self, config: Config, symbol_map: SymbolMap):
        """
        Initialize the BrokerClient instance.

        Args:
            config (Config): Configuration object containing broker connection details.
            symbol_map (SymbolMap): Mapping of symbols to broker-specific details.
        """
        self.logger = SystemLogger.get_logger()
        self.app = BrokerApp(symbol_map)

        self.host = config.broker["host"]
        self.port = int(config.broker["port"])
        self.clientId = config.broker["client_id"]
        self.account = config.broker["account_id"]
        self.lock = threading.Lock()  # create a lock

    # -- Helper --
    def _websocket_connection(self) -> None:
        """
        Establish a websocket connection with the broker's API.
        """
        self.app.connect(self.host, self.port, self.clientId)
        self.app.run()

    def _get_valid_id(self):
        """
        Get the next valid order ID.

        Returns:
            int: The next valid order ID.
        """
        with self.lock:
            current_valid_id = self.app.next_valid_order_id
            self.app.next_valid_order_id += 1
            return current_valid_id

    def _manange_subscription_to_account_updates(
        self,
        subscribe: bool,
    ) -> None:
        """
        Manage subscription to account updates.

        Args:
            subscribe (bool): Flag indicating whether to subscribe or unsubscribe.
        """
        self.app.reqAccountUpdates(subscribe=subscribe, acctCode=self.account)

    def _get_initial_active_orders(self):
        """
        Request initial active orders from the broker's API.
        """
        self.app.reqOpenOrders()

    # -- Connection --
    def connect(self) -> None:
        """
        Connect to the broker's API.
        """
        thread = threading.Thread(
            target=self._websocket_connection,
            daemon=True,
        )
        thread.start()

        # Waiting for confirmation of connection
        self.logger.info("Waiting For Broker Connection...")
        self.app.connected_event.wait()

        #  Waiting for next valid id to be returned
        self.app.valid_id_event.wait()

        # Waiting for initial download of account information and positions
        self._manange_subscription_to_account_updates(subscribe=True)
        self.app.account_download_event.wait()

        # Wating for initial open orders, need to explicatly call, as open orders not autmatically returned if no orders
        self._get_initial_active_orders()
        self.app.open_orders_event.wait()

    def disconnect(self) -> None:
        """
        Disconnect from the broker's API.
        """
        self._manange_subscription_to_account_updates(subscribe=False)
        self.app.disconnect()

    def is_connected(self) -> bool:
        """
        Check if the client is connected to the broker's API.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.app.isConnected()

    # -- Orders --
    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        event,
    ) -> None:
        """
        Handle new order events from the event queue and initiate order processing.

        Args:
            subject (Subject): The subject associated with the event.
            event_type (EventType): The type of the event.
            event (OrderEvent): The event containing order details for execution.

        Raises:
            ValueError: If the event is not of type OrderEvent.
        """
        if event_type == EventType.ORDER_CREATED:
            if not isinstance(event, OrderEvent):
                raise ValueError(
                    "'event' must be of type OrderEvent instance."
                )
            self.handle_order(event)

    def handle_order(self, event: OrderEvent) -> None:
        """
        Handle placing orders.

        Args:
            event (OrderEvent): The event containing the contract and order details.
        """
        orderId = self._get_valid_id()
        try:
            self.app.placeOrder(
                orderId=orderId,
                contract=event.contract,
                order=event.order.order,
            )
        except Exception as e:
            raise e

    def cancel_order(self, orderId: int) -> None:
        """
        Cancel an order.

        Args:
            orderId (int): The ID of the order to be canceled.
        """
        self.app.cancelOrder(orderId=orderId)

    # -- Account request --
    def request_account_summary(self) -> None:
        """
        Request account summary.

        Raises:
            Exception: If an error occurs while requesting the account summary.
        """
        # Get a unique request identifier
        reqId = self._get_valid_id()

        # Tags for request
        account_info_keys = Account.get_account_key_mapping().keys()
        tags_string = ",".join(account_info_keys)

        try:
            self.app.reqAccountSummary(reqId, "All", tags_string)
        except Exception as e:
            self.logger.error(f"Error requesting account summary: {e}")
            raise

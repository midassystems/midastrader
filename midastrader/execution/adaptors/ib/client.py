# client.py
import threading
import queue
from ibapi.contract import Contract

from midastrader.structs.events import OrderEvent
from midastrader.structs.account import Account
from midastrader.structs.symbol import SymbolMap
from midastrader.execution.adaptors.ib.wrapper import BrokerApp
from midastrader.execution.adaptors.base import ExecutionAdapter
from midastrader.message_bus import MessageBus, EventType
from midastrader.utils.logger import SystemLogger


class IBAdaptor(ExecutionAdapter):
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

    def __init__(self, symbol_map: SymbolMap, bus: MessageBus, **kwargs):
        """
        Initialize the BrokerClient instance.

        Args:
            config (Config): Configuration object containing broker connection details.
            symbol_map (SymbolMap): Mapping of symbols to broker-specific details.
        """
        super().__init__(symbol_map, bus)
        self.logger = SystemLogger.get_logger()

        # self.logger = SystemLogger.get_logger()
        self.app = BrokerApp(symbol_map, bus)
        self.host = kwargs["host"]
        self.port = int(kwargs["port"])
        self.clientId = kwargs["client_id"]
        self.account = kwargs["account_id"]
        self.lock = threading.Lock()  # create a lock
        self.validated_contracts = {}

        # Subscriptions
        self.orders_queue = self.bus.subscribe(EventType.ORDER)

    def process(self):
        self.connect()

        while not self.shutdown_event.is_set():
            try:
                event = self.orders_queue.get()
                self.handle_order(event)
            except queue.Empty:
                continue

        self.cleanup()

    def cleanup(self):
        """
        Main processing loop that streams data and handles EOD synchronization.
        """
        self.logger.info("Data Engine - stream done")

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

        # Validate Contracts
        for symbol in self.symbols_map.symbols:
            if not self.validate_contract(symbol.contract):
                raise RuntimeError(f"{symbol.broker_ticker} invalid contract.")

        self.logger.info("IBBrokerAdaptor running ...")
        self.running.set()

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

    # -- Validate Contracts --
    def validate_contract(self, contract: Contract) -> bool:
        """
        Validates a contract with Interactive Brokers.

        Behavior:
            - Checks if the contract is already validated.
            - If not validated, sends a request to Interactive Brokers for validation.
            - Updates `validated_contracts` upon successful validation.

        Args:
            contract (Contract): The `Contract` object to be validated.

        Returns:
            bool: `True` if the contract is successfully validated, otherwise `False`.

        Raises:
            ValueError: If the provided `contract` is not an instance of `Contract`.
        """
        if not isinstance(contract, Contract):
            raise ValueError("'contract' must be of type Contract instance.")

        # Check if the contract is already validated
        if self._is_contract_validated(contract):
            self.logger.info(f"Contract {contract.symbol} already validated.")
            return True

        # Reset the validation attribute in case it has been used before
        self.app.is_valid_contract = None
        self.app.validate_contract_event.clear()

        # Request contract details from IB
        reqId = self._get_valid_id()
        self.app.reqContractDetails(reqId=reqId, contract=contract)
        self.app.validate_contract_event.wait()

        # Store the validated contract if it's valid
        if self.app.is_valid_contract:
            self.validated_contracts[contract.symbol] = contract
            self.logger.info(
                f"Contract {contract.symbol} validated successfully."
            )
        else:
            self.logger.warning(
                f"Contract {contract.symbol} validation failed."
            )

        return self.app.is_valid_contract

    def _is_contract_validated(self, contract: Contract) -> bool:
        """
        Checks if a contract has already been validated.

        Args:
            contract (Contract): The `Contract` object to check for validation.

        Returns:
            bool: `True` if the contract has already been validated, otherwise `False`.
        """
        return contract.symbol in self.validated_contracts

    # -- Orders --
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

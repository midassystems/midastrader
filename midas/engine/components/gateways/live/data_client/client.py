# client.py
import logging
import threading
from queue import Queue
from decouple import config
from ibapi.contract import Contract
from midas.engine.components.order_book import OrderBook
from midas.market_data import MarketDataType
from midas.engine.components.gateways.live.data_client.wrapper import DataApp
from midas.engine.components.gateways.base_data_client import BaseDataClient


class DataClient(BaseDataClient):
    """
    This class manages the data connection to the Interactive Brokers (IB) server. It handles various data requests like
    quotes and bars through a WebSocket connection, ensuring thread-safe operations with the help of locks.

    Attributes:
    - event_queue (Queue): A queue used for managing asynchronous events received from the IB server.
    - order_book (OrderBook): An instance of the OrderBook class to maintain and update the order book with live data.
    - logger (logging.Logger): A logger for recording operational logs, errors, or informational messages.
    - host (str): The hostname or IP address of the IB data server.
    - port (int): The port number on which the IB data server is listening.
    - clientId (str): A unique identifier for the client connecting to the IB data server.
    - account (str): The identifier for the Interactive Brokers account associated with this connection.
    - lock (Lock): A threading lock to ensure that certain operations are thread-safe.

    Methods:
    - connect(): Establishes a WebSocket connection to the Interactive Brokers server and initializes session parameters.
    - disconnect(): Closes the WebSocket connection to the IB server.
    - is_connected(): Checks if the client is currently connected to the IB server.
    - get_data(data_type: MarketDataType, contract: Contract): Requests data based on the specified market data type and financial contract.
    - stream_5_sec_bars(contract: Contract): Initiates a stream of 5-second bars for the specified contract.
    - cancel_all_bar_data(): Cancels all active 5-second bar data streams.
    - stream_quote_data(contract: Contract): Starts streaming quote data for the specified contract.
    - cancel_all_quote_data(): Cancels all active quote data streams.
    """

    def __init__(
        self,
        event_queue: Queue,
        order_book: OrderBook,
        logger: logging.Logger,
        host=config("HOST"),
        port=config("PORT"),
        clientId=config("DATA_CLIENT_ID"),
        ib_account=config("IB_ACCOUNT"),
    ):
        """
        Initializes the DataClient instance.

        Parameters:
        - event_queue (Queue): The queue used for processing events from the IB server.
        - order_book (OrderBook): The order book managing live order data.
        - logger (logging.Logger): Used for logging messages, errors, and informational logs.
        - host (str): Hostname or IP address of the IB server.
        - port (int): Port number on which the IB server is accessible.
        - clientId (str): Unique client identifier for this connection.
        - ib_account (str): IB account identifier for which data will be fetched.
        """
        self.logger = logger
        self.app = DataApp(event_queue, order_book, logger)
        self.host = host
        self.port = int(port)
        self.clientId = clientId
        self.account = ib_account

        self.lock = threading.Lock()  # create a lock

    # -- Helper --
    def _websocket_connection(self):
        """ "Internal method to manage the WebSocket connection lifecycle."""
        self.app.connect(self.host, self.port, self.clientId)
        self.app.run()

    def _get_valid_id(self) -> int:
        """ "
        Retrieves and increments the next valid order ID in a thread-safe manner.

        Returns:
        - int: The next available valid ID for use in requests.
        """
        with self.lock:
            current_valid_id = self.app.next_valid_order_id
            self.app.next_valid_order_id += 1
            return current_valid_id

    # -- Connection --
    def connect(self):
        """
        Starts a new thread to establish a WebSocket connection to the Interactive Brokers server and waits for the
            connection to be confirmed. It also waits for the next valid order ID to be initialized before proceeding.
        """
        thread = threading.Thread(
            target=self._websocket_connection, daemon=True
        )
        thread.start()

        # Waiting for confirmation of connection
        self.logger.info("Waiting For Data Connection...")
        self.app.connected_event.wait()

        #  Waiting for next valid id to be returned
        self.app.valid_id_event.wait()

    def disconnect(self):
        """Closes the WebSocket connection to the Interactive Brokers server."""
        self.app.disconnect()

    def is_connected(self) -> bool:
        """
        Check if the client is connected to the broker's API.

        Returns:
        - bool: True if connected, False otherwise.
        """
        return self.app.isConnected()

    # -- Data --
    def get_data(self, data_type: MarketDataType, contract: Contract):
        """
        Initiates data requests for the specified market data type and contract. Raises an error if an unsupported
        data type is specified.

        Parameters:
        - data_type (MarketDataType): The type of market data to request (e.g., QUOTE, BAR).
        - contract (Contract): The contract for which the data is requested.
        """
        if data_type == MarketDataType.QUOTE:
            self.stream_quote_data(contract)
        elif data_type == MarketDataType.BAR:
            self.stream_5_sec_bars(contract)
        else:
            raise ValueError(
                f"'data_type' must be of type MarketDataType enum."
            )

    def stream_5_sec_bars(self, contract: Contract):
        """
        Initiates a real-time data stream of 5-second bars for a specified contract.

        Parameters:
        - contract (Contract): The contract for which the 5-second bars are requested.
        """
        reqId = self._get_valid_id()

        # TODO: may not need the reqId check
        if (
            reqId not in self.app.reqId_to_symbol_map.keys()
            and contract.symbol not in self.app.reqId_to_symbol_map.values()
        ):
            self.app.reqRealTimeBars(
                reqId=reqId,
                contract=contract,
                barSize=5,
                whatToShow="TRADES",
                useRTH=False,
                realTimeBarsOptions=[],
            )
            self.app.reqId_to_symbol_map[reqId] = contract.symbol
            self.logger.info(f"Started 5 sec bar data stream for {contract}.")
        else:
            self.logger.error(
                f"Data stream already established for {contract}."
            )

    def cancel_all_bar_data(self):
        """Cancels all active 5-second bar data streams and clears related mappings."""
        # Cancel real time bars for all reqId ** May not all be on bar data **
        for reqId in self.app.reqId_to_symbol_map.keys():
            self.app.cancelRealTimeBars(reqId)
        self.app.reqId_to_symbol_map.clear()

    def stream_quote_data(self, contract: Contract):
        """
        Starts a real-time quote data stream for the specified contract.

        Parameters:
        - contract (Contract): The contract for which the quote data is requested.
        """
        reqId = self._get_valid_id()

        if (
            reqId not in self.app.reqId_to_symbol_map.keys()
            and contract.symbol not in self.app.reqId_to_symbol_map.values()
        ):
            self.app.reqMktData(
                reqId=reqId,
                contract=contract,
                genericTickList="",
                snapshot=False,
                regulatorySnapshot=False,
                mktDataOptions=[],
            )
            self.app.reqId_to_symbol_map[reqId] = contract.symbol
            self.logger.info(
                f"Requested top of book tick data stream for {contract}."
            )

        self.logger.error(f"Data stream already established for {contract}.")

    def cancel_all_quote_data(self):
        """
        Cancels all active quote data streams and clears the associated mappings.
        """
        # Cancel real tiem bars for all reqId ** May not all be on bar data **
        for reqId in self.app.reqId_to_symbol_map.keys():
            self.app.cancelMktData(reqId)

        self.app.reqId_to_symbol_map.clear()

    # def cancel_market_data_stream(self,contract:Contract):
    #     for key, value in self.app.market_data_top_book.items():
    #         if value['CONTRACT'] == contract:
    #             self.app.cancelMktData(reqId=key)
    #             remove_key = key
    #     del self.app.market_data_top_book[key]

    # def get_top_book_market_data(self):
    #     return self.app.market_data_top_book

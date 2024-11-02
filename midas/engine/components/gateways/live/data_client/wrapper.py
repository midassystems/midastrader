import os
from datetime import datetime
import threading
from typing import Union, Optional
from decimal import Decimal
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import ContractDetails
from mbn import OhlcvMsg
from midas.utils.logger import SystemLogger
from midas.engine.components.observer.base import Subject, EventType
from ibapi.ticktype import TickType
from ibapi.common import TickAttrib
import time


class DataApp(EWrapper, EClient, Subject):
    """
    A specialized class that handles the interaction with the Interactive Brokers (IB) API, managing the flow of data,
    handling errors, and executing event-driven responses. It extends functionality from both EWrapper and EClient
    to integrate event handling and client functionalities.

    Attributes:
    - event_queue (Queue): Queue to manage asynchronous event-driven data handling.
    - order_book (OrderBook): A data structure to maintain and update market order information.
    - logger (logging.Logger): Logger for capturing and reporting log messages.
    - next_valid_order_id (int): Tracks the next valid order ID provided by the IB server.
    - is_valid_contract (bool): Indicator of whether a contract is valid after a contract details request.
    - reqId_to_symbol_map (dict): Maps request IDs to symbol names for tracking data requests.
    - market_data_top_book (dict): Stores top-of-the-book market data indexed by request IDs.
    - current_bar_data (dict): Holds the latest bar data received from the server, reset after each update.
    - connected_event (threading.Event): Event to signal successful connection to the server.
    - valid_id_event (threading.Event): Event to signal receipt of the next valid order ID.
    - validate_contract_event (threading.Event): Event to signal the completion of contract validation.
    - next_valid_order_id_lock (threading.Lock): Lock to ensure thread-safe operations on next_valid_order_id.
    """

    def __init__(self, tick_interval: Optional[int]):
        """
        Initializes a new instance of the DataApp, setting up the necessary attributes for managing data interactions
        with the Interactive Brokers API.

        Parameters:
        - event_queue (Queue): Queue for handling asynchronous events such as market data updates.
        - order_book (OrderBook): Manages and updates market order data.
        - logger (logging.Logger): Used for logging messages, errors, and other important information.
        """
        EClient.__init__(self, self)
        Subject.__init__(self)
        self.logger = SystemLogger.get_logger()

        #  Data Storage
        self.next_valid_order_id = None
        self.is_valid_contract = None
        self.reqId_to_instrument = {}
        self.tick_data = {}

        # Event Handling
        self.connected_event = threading.Event()
        self.valid_id_event = threading.Event()
        self.validate_contract_event = threading.Event()

        # Thread Locks
        self.next_valid_order_id_lock = threading.Lock()

        # Tick interval updater
        self.update_interval = (
            tick_interval  # Seconds interval for pushing the event
        )
        self.is_running = True
        self.timer_thread = threading.Thread(
            target=self._run_timer,
            daemon=True,
        )
        self.timer_thread.start()

    def _run_timer(self):
        """A continuously running timer in a separate thread that checks every 5 seconds."""
        while self.is_running:
            time.sleep(self.update_interval)
            self.push_market_event()

    def stop(self):
        """Gracefully stop the timer thread and other resources."""
        self.is_running = False
        self.timer_thread.join()
        self.logger.info("Shutting down the DataApp.")

    def error(
        self,
        reqId: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson: Union[str, None] = None,
    ):
        """
        Handles errors reported by the Interactive Brokers server. Logs critical errors and manages application state
        changes based on specific error codes.

        Parameters:
        - reqId (int): The request ID associated with the error, if applicable.
        - errorCode (int): The error code provided by the Interactive Brokers server.
        - errorString (str): A descriptive string of the error.
        - advancedOrderRejectJson (str, optional): Additional JSON-formatted data about the rejection of advanced orders.
        """
        super().error(reqId, errorCode, errorString)
        if errorCode == 502:  # Error for wrong port
            self.logger.critical(
                f"Port Error : {errorCode} incorrect port entered."
            )
            os._exit(0)
        elif errorCode == 200:  # Error for invalid contract.
            self.logger.critical(f"{errorCode} : {errorString}")
            self.is_valid_contract = False
            self.validate_contract_event.set()

    #### wrapper function to signifying completion of successful connection.
    def connectAck(self):
        """
        Acknowledges a successful connection to the Interactive Brokers server. Logs this event and sets an event flag
        to signal other parts of the application that the connection has been established.
        """
        super().connectAck()
        self.logger.info("Established Data Connection")
        self.connected_event.set()

    #### wrapper function for disconnect() -> Signals disconnection.
    def connectionClosed(self):
        """
        Handles the event of a connection closure with the Interactive Brokers server. Logs the disconnection and cleans
        up relevant data structures if necessary.
        """
        super().connectionClosed()
        self.logger.info("Closed Data Connection.")

    #### wrapper function for reqIds() -> This function manages the Order ID.
    def nextValidId(self, orderId: int):
        """
        Receives and updates the next valid order ID from the Interactive Brokers server. Ensures thread-safe access to
        this critical resource.

        Parameters:
        - orderId (int): The next valid order ID provided by the server.
        """
        super().nextValidId(orderId)
        with self.next_valid_order_id_lock:
            self.next_valid_order_id = orderId

        self.logger.info(f"Next Valid Id {self.next_valid_order_id}")
        self.valid_id_event.set()

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        """
        Receives and processes contract details, confirming the validity of a contract based on a request.

        Parameters:
        - reqId (int): The request ID associated with the contract details.
        - contractDetails (ContractDetails): The detailed information about the contract.
        """
        self.is_valid_contract = True

    def contractDetailsEnd(self, reqId: int):
        """
        Signals the end of processing for contract details. Sets an event to indicate that validation of the contract
        is complete and further actions can proceed.

        Parameters:
        - reqId (int): The request ID associated with the end of the contract details.
        """
        self.validate_contract_event.set()

    def realtimeBar(
        self,
        reqId: int,
        time: int,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: Decimal,
        wap: Decimal,
        count: int,
    ):
        """
        Processes and updates the real-time bar data for a specific contract. This data is critical for live trading decisions.

        Parameters:
        - reqId (int): The request ID associated with this data stream.
        - time (int): The timestamp for the bar data.
        - open (float): The opening price in the bar.
        - high (float): The highest price in the bar.
        - low (float): The lowest price in the bar.
        - close (float): The closing price in the bar.
        - volume (Decimal): The volume of trading during the bar.
        - wap (float): The weighted average price during the bar.
        - count (int): The count of trades during the bar.
        """
        super().realtimeBar(
            reqId,
            time,
            open_,
            high,
            low,
            close,
            volume,
            wap,
            count,
        )
        instrument_id = self.reqId_to_instrument[reqId]

        bar = OhlcvMsg(
            instrument_id=instrument_id,
            ts_event=int(time * 1e9),
            open=int(open_ * 1e9),
            high=int(high * 1e9),
            low=int(low * 1e9),
            close=int(close * 1e9),
            volume=int(volume),
        )
        self.notify(EventType.MARKET_DATA, bar)

    def tickPrice(
        self,
        reqId: int,
        tickType: TickType,
        price: float,
        attrib: TickAttrib,
    ):
        """Market data tick price callback. Handles all price related ticks."""
        # print(tickType)
        if tickType == 1:  # BID
            # print("dbid")
            self.tick_data[reqId].levels[0].bid_px = int(price * 1e9)
            # print(self.tick_data)
            self.logger.info(f"BID : {reqId} : {price}")
        elif tickType == 2:  # ASK
            self.tick_data[reqId].levels[0].ask_px = int(price * 1e9)
            self.logger.info(f"ASK : {reqId} : {price}")
        elif tickType == 4:
            self.tick_data[reqId].price = int(price * 1e9)
            self.logger.info(f"Last : {reqId} :  {price}")

    def tickSize(self, reqId: int, tickType, size: Decimal):
        """Market data tick size callback. Handles all size-related ticks."""

        if tickType == 0:  # BID_SIZE
            self.tick_data[reqId].levels[0].bid_sz = int(size)
            self.logger.info(f"BID SIZE : {reqId} : {size}")
        elif tickType == 3:  # ASK_SIZE
            self.tick_data[reqId].levels[0].ask_sz = int(size)
            self.logger.info(f"ASK SIZE : {reqId} : {size}")
        elif tickType == 5:  # Last_SIZE
            self.tick_data[reqId].size = int(size)
            self.logger.info(f"Last SIZE : {reqId} : {size}")

    def tickString(self, reqId: int, tickType: TickType, value: str):
        """Handles string-based market data updates."""

        if tickType == 45:  # TIMESTAMP
            self.tick_data[reqId].hd.ts_event = int(int(value) * 1e9)
            self.logger.info(f"Time Last : {reqId} : {value}")
            self.logger.info(f"Recv :{datetime.now()}")

    def push_market_event(self):
        """Pushes a market event after processing the tick data."""

        self.logger.info(f"Market event pushed at {datetime.now()}")

        # Process the latest tick data (This is just an example)
        for _, data in self.tick_data.items():
            # Notify system with the processed tick data
            self.notify(EventType.MARKET_DATA, data)

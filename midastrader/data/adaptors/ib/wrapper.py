import time
import os
from datetime import datetime
from mbn import OhlcvMsg
import threading
from typing import Union, Optional
from decimal import Decimal
from ibapi.common import TickAttrib
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import ContractDetails

from midastrader.message_bus import MessageBus, EventType
from midastrader.utils.logger import SystemLogger


class DataApp(EWrapper, EClient):
    """
    A specialized class that handles interaction with the Interactive Brokers (IB) API. Manages data flow,
    handles errors, and executes event-driven responses by integrating functionality from both EWrapper and EClient.

    Attributes:
        order_book (OrderBook): Data structure to maintain and update market order information.
        logger (logging.Logger): Logger for capturing and reporting log messages.
        next_valid_order_id (int): Tracks the next valid order ID provided by the IB server.
        is_valid_contract (bool): Indicates if a contract is valid after a contract details request.
        reqId_to_instrument (dict): Maps request IDs to instrument IDs for tracking data requests.
        tick_data (dict): Stores tick data indexed by request IDs.
        connected_event (threading.Event): Event to signal successful connection to the server.
        valid_id_event (threading.Event): Event to signal receipt of the next valid order ID.
        validate_contract_event (threading.Event): Event to signal the completion of contract validation.
        next_valid_order_id_lock (threading.Lock): Lock to ensure thread-safe operations on next_valid_order_id.
        update_interval (int): Interval in seconds for pushing market events.
        is_running (bool): Indicates if the timer thread is running.
        timer_thread (threading.Thread): Timer thread for periodic operations.
    """

    def __init__(self, message_bus: MessageBus, tick_interval: Optional[int]):
        """
        Initializes a new instance of DataApp, setting up attributes for managing data interactions with IB API.

        Args:
            tick_interval (Optional[int]): Interval in seconds for pushing market events.
        """
        EClient.__init__(self, self)
        self.logger = SystemLogger.get_logger()
        self.bus = message_bus

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

        # Tick interval updater FOR TICK DATA
        # Seconds interval for pushing the event
        # self.update_interval = tick_interval
        # self.is_running = True
        # self.timer_thread = threading.Thread(
        #     target=self._run_timer, daemon=True
        # )
        # self.timer_thread.start()

    def _run_timer(self) -> None:
        """
        Continuously runs a timer in a separate thread that triggers every update_interval seconds.
        """
        while self.is_running:
            time.sleep(self.update_interval)
            self.push_market_event()

    def stop(self) -> None:
        """
        Gracefully stops the timer thread and other resources.
        """
        self.is_running = False
        self.timer_thread.join()
        self.logger.info("Shutting down the DataApp.")

    def error(
        self,
        reqId: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson: Union[str, None] = None,
    ) -> None:
        """
        Handles errors reported by the IB server. Logs critical errors and manages application state based on error codes.

        Args:
            reqId (int): Request ID associated with the error, if applicable.
            errorCode (int): Error code provided by the IB server.
            errorString (str): Description of the error.
            advancedOrderRejectJson (Union[str, None], optional): JSON data about rejection of advanced orders.
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
    def connectAck(self) -> None:
        """
        Acknowledges a successful connection to the IB server. Logs this event and signals other parts of the application.
        """
        super().connectAck()
        self.logger.info("Established Data Connection")
        self.connected_event.set()

    #### wrapper function for disconnect() -> Signals disconnection.
    def connectionClosed(self) -> None:
        """
        Handles the event of a connection closure with the IB server. Logs the disconnection and cleans up resources.
        """
        super().connectionClosed()
        self.logger.info("Closed Data Connection.")

    #### wrapper function for reqIds() -> This function manages the Order ID.
    def nextValidId(self, orderId: int) -> None:
        """
        Receives and updates the next valid order ID from the IB server. Ensures thread-safe access to the resource.

        Args:
            orderId (int): Next valid order ID provided by the server.
        """
        super().nextValidId(orderId)
        with self.next_valid_order_id_lock:
            self.next_valid_order_id = orderId

        self.logger.info(f"Next Valid Id {self.next_valid_order_id}")
        self.valid_id_event.set()

    def contractDetails(
        self,
        reqId: int,
        contractDetails: ContractDetails,
    ) -> None:
        """
        Processes contract details, confirming the validity of a contract based on a request.

        Args:
            reqId (int): Request ID associated with the contract details.
            contractDetails (ContractDetails): Detailed information about the contract.
        """
        self.is_valid_contract = True

    def contractDetailsEnd(self, reqId: int) -> None:
        """
        Signals the end of processing for contract details. Indicates that validation of the contract is complete.

        Args:
            reqId (int): Request ID associated with the end of the contract details.
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
    ) -> None:
        """
        Processes and updates real-time bar data for a specific contract.

        Args:
            reqId (int): Request ID associated with this data stream.
            time (int): Timestamp for the bar data.
            open_ (float): Opening price in the bar.
            high (float): Highest price in the bar.
            low (float): Lowest price in the bar.
            close (float): Closing price in the bar.
            volume (Decimal): Trading volume during the bar.
            wap (Decimal): Weighted average price during the bar.
            count (int): Number of trades during the bar.
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
        self.bus.publish(EventType.DATA, bar)

    def tickPrice(
        self,
        reqId: int,
        tickType: int,
        price: float,
        attrib: TickAttrib,
    ) -> None:
        """
        Callback for market data tick price. Handles all price-related ticks.

        Args:
            reqId (int): Request ID associated with the tick.
            tickType (TickType): Type of the tick (e.g., BID, ASK, LAST).
            price (float): Price value of the tick.
            attrib (TickAttrib): Additional attributes of the tick.
        """
        if tickType == 1:  # BID
            self.tick_data[reqId].bid_px = int(price * 1e9)
            self.logger.debug(f"BID : {reqId} : {price}")
        elif tickType == 2:  # ASK
            self.tick_data[reqId].ask_px = int(price * 1e9)
            self.logger.debug(f"ASK : {reqId} : {price}")
        elif tickType == 4:
            self.tick_data[reqId].price = int(price * 1e9)
            self.logger.debug(f"Last : {reqId} :  {price}")

    def tickSize(self, reqId: int, tickType: int, size: Decimal) -> None:
        """
        Callback for market data tick size. Handles all size-related ticks.

        Args:
            reqId (int): Request ID associated with the tick.
            tickType (TickType): Type of the tick (e.g., BID_SIZE, ASK_SIZE, LAST_SIZE).
            size (Decimal): Size value of the tick.
        """
        if tickType == 0:  # BID_SIZE
            self.tick_data[reqId].bid_sz = int(size)
            self.logger.debug(f"BID SIZE : {reqId} : {size}")
        elif tickType == 3:  # ASK_SIZE
            self.tick_data[reqId].ask_sz = int(size)
            self.logger.debug(f"ASK SIZE : {reqId} : {size}")
        elif tickType == 5:  # Last_SIZE
            self.tick_data[reqId].size = int(size)
            self.logger.debug(f"Last SIZE : {reqId} : {size}")

    def tickString(self, reqId: int, tickType: int, value: str) -> None:
        """
        Handles string-based market data updates.

        Args:
            reqId (int): Request ID associated with the tick.
            tickType (TickType): Type of the tick (e.g., TIMESTAMP).
            value (str): String value of the tick.
        """
        if tickType == 45:  # TIMESTAMP
            self.tick_data[reqId].ts_event = int(int(value) * 1e9)
            self.logger.debug(f"Time Last : {reqId} : {value}")
            self.logger.debug(f"Recv :{datetime.now()}")

    def push_market_event(self) -> None:
        """
        Pushes a market event after processing the tick data.

        This method processes the latest tick data and notifies the system with the processed data.
        """

        self.logger.info(f"Market event pushed at {datetime.now()}")

        # Process the latest tick data (This is just an example)
        for _, data in self.tick_data.items():
            self.bus.publish(EventType.DATA, data)

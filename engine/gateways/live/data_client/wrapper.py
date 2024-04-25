import os
import logging
import threading
import numpy as np
from queue import Queue
from decimal import Decimal
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import ContractDetails

from engine.order_book import OrderBook
from shared.market_data import BarData, QuoteData


class DataApp(EWrapper, EClient):
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
    def __init__(self, event_queue: Queue, order_book: OrderBook, logger: logging.Logger):
        """
        Initializes a new instance of the DataApp, setting up the necessary attributes for managing data interactions
        with the Interactive Brokers API.

        Parameters:
        - event_queue (Queue): Queue for handling asynchronous events such as market data updates.
        - order_book (OrderBook): Manages and updates market order data.
        - logger (logging.Logger): Used for logging messages, errors, and other important information.
        """
        EClient.__init__(self, self)
        self.event_queue = event_queue
        self.logger = logger
        self.order_book = order_book

        #  Data Storage
        self.next_valid_order_id = None
        self.is_valid_contract = None
        self.reqId_to_symbol_map = {}
        self.market_data_top_book = {}
        self.current_bar_data = {}

        # Event Handling
        self.connected_event = threading.Event()
        self.valid_id_event = threading.Event()
        self.validate_contract_event = threading.Event()

        # Thread Locks
        self.next_valid_order_id_lock = threading.Lock()

    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str=None):
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
        if errorCode == 502: # Error for wrong port
            self.logger.critical(f"Port Error : {errorCode} incorrect port entered.")
            os._exit(0)
        elif errorCode == 200: # Error for invalid contract.
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
        self.logger.info('Established Data Connection')
        self.connected_event.set()

    #### wrapper function for disconnect() -> Signals disconnection.
    def connectionClosed(self):
        """
        Handles the event of a connection closure with the Interactive Brokers server. Logs the disconnection and cleans
        up relevant data structures if necessary.
        """
        super().connectionClosed()
        self.logger.info('Closed Data Connection.')

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
    
    def realtimeBar(self, reqId: int, time: int, open: float, high: float, low: float, close: float, volume: Decimal, wap: float, count: int):
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
        super().realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        """ Updates the real time 5 seconds bars """
        symbol = self.reqId_to_symbol_map[reqId]

        timestamp= np.uint64(time * 1e9)
        
        new_bar_entry = BarData(ticker=symbol, timestamp= timestamp, open=Decimal(open), high=Decimal(high), low=Decimal(low), close=Decimal(close), volume=np.uint64(volume))
        self.current_bar_data[symbol] = new_bar_entry
        
        if len(self.current_bar_data) == len(self.reqId_to_symbol_map):
            self.order_book.update_market_data(timestamp=timestamp, data=self.current_bar_data)
            # market_data_event = MarketEvent(timestamp=time, data=self.current_bar_data)
            # self.event_queue.put(market_data_event)
            # Reset current bar data for the next bar
            self.current_bar_data = {}

    
    # def tickPrice(self, reqId: int, tickType, price: float, attrib):
    #     """Market data tick price callback. Handles all price related ticks."""
    #     super().tickPrice(reqId, tickType, price, attrib)
        
    #     if reqId not in self.market_data_top_book:
    #         self.market_data_top_book[reqId] = TickData(reqId)
        
    #     if tickType == 1:  # BID
    #         self.market_data_top_book[reqId].BID = price
    #     elif tickType == 2:  # ASK
    #         self.market_data_top_book[reqId].ASK = price

    #     self.logger.info(vars(self.market_data_top_book[reqId]))

    # def tickSize(self, reqId: int, tickType, size: int):
    #     """Market data tick size callback. Handles all size-related ticks."""
    #     super().tickSize(reqId, tickType, size)

    #     if reqId not in self.market_data_top_book:
    #         self.market_data_top_book[reqId] = TickData(reqId)
        
    #     if tickType == 0:  # BID_SIZE
    #         self.market_data_top_book[reqId].BID_SIZE = size
    #     elif tickType == 3:  # ASK_SIZE
    #         self.market_data_top_book[reqId].ASK_SIZE = size
            
    #     self.logger.info(vars(self.market_data_top_book[reqId]))

    # def tickString(self, reqId: int, tickType, value: str):
    #     """Handles string-based market data updates."""
    #     super().tickString(reqId, tickType, value)

    #     if reqId not in self.market_data_top_book:
    #         self.market_data_top_book[reqId] = TickData(reqId)
        
    #     if tickType == 45:  # TIMESTAMP
    #         self.market_data_top_book[reqId].TIMESTAMP = value

    #     self.logger.info(vars(self.market_data_top_book[reqId]))

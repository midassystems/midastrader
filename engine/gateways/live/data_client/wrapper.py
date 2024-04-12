import os
import logging
import threading
from queue import Queue
from decimal import Decimal
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import ContractDetails

from engine.events import MarketEvent, BarData
from engine.order_book import OrderBook


class DataApp(EWrapper, EClient):
    
    def __init__(self, event_queue:Queue, order_book:OrderBook, logger:logging.Logger):
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
        super().connectAck()
        self.logger.info('Established Data Connection')
        self.connected_event.set()

    #### wrapper function for disconnect() -> Signals disconnection.
    def connectionClosed(self):
        super().connectionClosed()
        self.logger.info('Closed Data Connection.')

    #### wrapper function for reqIds() -> This function manages the Order ID.
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        with self.next_valid_order_id_lock:
            self.next_valid_order_id = orderId
        
        self.logger.info(f"Next Valid Id {self.next_valid_order_id}")
        self.valid_id_event.set()

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        self.is_valid_contract = True

    def contractDetailsEnd(self, reqId: int):
        self.validate_contract_event.set()
    
    def realtimeBar(self, reqId: int, time: int, open: float, high: float, low: float, close: float, volume: Decimal, wap: float, count: int):
        super().realtimeBar(reqId, time, open, high, low, close, volume, wap, count)
        """ Updates the real time 5 seconds bars """
        symbol = self.reqId_to_symbol_map[reqId]

        new_bar_entry = BarData(time, open, high, low, close, float(volume))
        self.current_bar_data[symbol] = new_bar_entry
        
        if len(self.current_bar_data) == len(self.reqId_to_symbol_map):
            self.order_book.update_market_data(data=self.current_bar_data, timestamp=time)
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

# client.py
import logging
import threading
from queue import Queue
from decouple import config
from ibapi.contract import Contract

from .wrapper import DataApp
from midas.events import MarketDataType
from midas.order_book import OrderBook

class DataClient:

    def __init__(self, event_queue: Queue, order_book: OrderBook, logger: logging.Logger, host=config('HOST'), port=config('PORT'), clientId=config('DATA_CLIENT_ID'), ib_account =config('IB_ACCOUNT')):
        self.logger = logger
        self.app = DataApp(event_queue, order_book, logger)
        self.host = host
        self.port = int(port)
        self.clientId = clientId
        self.account = ib_account

        self.lock = threading.Lock()  # create a lock
    
    # -- Helper --
    def _websocket_connection(self):
        self.app.connect(self.host, self.port, self.clientId)
        self.app.run()

    def _get_valid_id(self): 
        with self.lock:
            current_valid_id = self.app.next_valid_order_id
            self.app.next_valid_order_id += 1
            return current_valid_id 

    # -- Connection --
    def connect(self):
        thread = threading.Thread(target=self._websocket_connection, daemon=True)
        thread.start()

        # Waiting for confirmation of connection
        self.logger.info('Waiting For Data Connection...')
        self.app.connected_event.wait()
        
        #  Waiting for next valid id to be returned
        self.app.valid_id_event.wait()

    def disconnect(self):
        self.app.disconnect()

    def is_connected(self):
        return self.app.isConnected()
    
    # -- Data --
    def get_data(self, data_type:MarketDataType, contract:Contract):
        if data_type == MarketDataType.QUOTE:
            self.stream_quote_data(contract)
        elif data_type == MarketDataType.BAR:
            self.stream_5_sec_bars(contract)
        else:
            raise ValueError(f"'data_type' must be of type MarketDataType enum.")

    def stream_5_sec_bars(self, contract:Contract):
        reqId = self._get_valid_id()

        # TODO: may not need the reqId check 
        if reqId not in self.app.reqId_to_symbol_map.keys() and contract.symbol not in self.app.reqId_to_symbol_map.values():
            self.app.reqRealTimeBars(reqId=reqId, contract=contract, barSize=5, whatToShow='TRADES', useRTH=False, realTimeBarsOptions=[])
            self.app.reqId_to_symbol_map[reqId] = contract.symbol
            self.logger.info(f"Started 5 sec bar data stream for {contract}.")
        else:
            self.logger.error(f"Data stream already established for {contract}.")

    def cancel_all_bar_data(self):
        # Cancel real time bars for all reqId ** May not all be on bar data ** 
        for reqId in self.app.reqId_to_symbol_map.keys():
            self.app.cancelRealTimeBars(reqId)
        self.app.reqId_to_symbol_map.clear()
        
    def stream_quote_data(self, contract:Contract):
        reqId = self._get_valid_id()
        
        if reqId not in self.app.reqId_to_symbol_map.keys() and contract.symbol not in self.app.reqId_to_symbol_map.values():
            self.app.reqMktData(reqId=reqId, contract=contract,genericTickList="", snapshot=False, regulatorySnapshot=False, mktDataOptions=[])
            self.app.reqId_to_symbol_map[reqId] = contract.symbol
            self.logger.info(f"Requested top of book tick data stream for {contract}.")
        
        self.logger.error(f"Data stream already established for {contract}.")

    def cancel_all_quote_data(self):
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







    
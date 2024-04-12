from queue import Queue
from typing import Dict, Union

from engine.observer import Subject, EventType
from engine.events import BarData, QuoteData, MarketDataType, MarketEvent, MarketData

class OrderBook(Subject):
    def __init__(self, data_type: MarketDataType, event_queue: Queue):
        super().__init__()

        if not isinstance(data_type, MarketDataType):
            raise TypeError("'data_type' must be of type MarketDataType enum.")
        
        self.event_queue = event_queue
        self.book : Dict[str, Union[BarData, QuoteData]] = {} # Example: {ticker : {'data': {Ask:{}, Bid:{}}, 'last_updated': timestamp}, ...}
        self.last_updated = None
        self.data_type = data_type

    def update_market_data(self, data: Dict[str, Union[BarData, QuoteData]], timestamp: int):
        """
        Process market data and generate trading signals.

        Parameters:
            data (Dict): The market data.
            timestamp (str): The timestamp of the data.
        """
        for ticker, market_data in data.items():
            if isinstance(market_data, BarData):
                self._insert_bar(ticker, market_data)
            elif isinstance(market_data, QuoteData):
                self._insert_or_update_quote(ticker, market_data, timestamp)

        self.last_updated = timestamp
        self.event_queue.put(MarketEvent(timestamp=timestamp, data=data))
        self.notify(EventType.MARKET_EVENT)  # update database
        
    def _insert_bar(self, ticker: str, data: MarketData):
        """
        Insert or update the data for a ticker along with the timestamp.

        Parameters:
            ticker (str): The ticker symbol.
            data (dict): The data to be stored for the ticker.
            timestamp (str): The timestamp when the data was received.
        """
        # Directly insert or update BarData
        self.book[ticker] = data

    def _insert_or_update_quote(self, ticker: str, quote_data: QuoteData, timestamp: int):
        self.book[ticker] = quote_data  # For keeping only the most recent quote:

    def current_price(self, ticker: str):
        if ticker in self.book:
            data = self.book[ticker]
            if self.data_type.value == MarketDataType.BAR.value:
                return data.close # returns close as it is most recent
            elif self.data_type.value == MarketDataType.QUOTE.value: 
                return (data.ask + data.bid) / 2 # returns a mid-price
        else:
            return None  # Ticker not found

    def current_prices(self) -> dict:
        prices = {}
        for key, data in self.book.items():
            if self.data_type.value == MarketDataType.BAR.value:
                prices[key] = data.close
            elif self.data_type.value == MarketDataType.QUOTE.value:
                prices[key] = (data.ask + data.bid) / 2 
        return prices
        
    def _modify(self):
        # Changing an old bar or order in the book
        pass
    def _cancellation(self):
        pass
        # remove a cancelled order from the book
    def retrieval(self):
        pass
        # makes for a fast access of a the current best price for a given symbol
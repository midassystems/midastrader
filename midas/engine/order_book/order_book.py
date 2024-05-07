from queue import Queue
from typing import Dict, Union

from midas.engine.events import  MarketEvent
from midas.engine.observer import Subject, EventType

from midas.shared.market_data import MarketData, MarketDataType, BarData, QuoteData


class OrderBook(Subject):
    """Manages market data updates and notifies observers about market changes."""
    def __init__(self, data_type: MarketDataType, event_queue: Queue):
        """
        Initializes the order book with a specific market data type and an event queue.

        Parameters:
        - data_type (MarketDataType): The type of data the order book will handle.
        - event_queue (Queue): The event queue to post market events to.
        """
        super().__init__()

        if not isinstance(data_type, MarketDataType):
            raise TypeError("'data_type' must be of type MarketDataType enum.")
        
        self.event_queue = event_queue
        self.book : Dict[str, Union[BarData, QuoteData]] = {} # Example: {ticker : {'data': {Ask:{}, Bid:{}}, 'last_updated': timestamp}, ...}
        self.last_updated = None
        self.data_type = data_type

    def update_market_data(self, data: Dict[str, Union[BarData, QuoteData]], timestamp: int) -> None:
        """
        Update the market data in the order book and notify observers of market events.

        Parameters:
        - data (Dict[str, Union[BarData, QuoteData]]): The market data to be updated.
        - timestamp (int): The timestamp when the data was updated.
        """
        for ticker, market_data in data.items():
            if isinstance(market_data, BarData):
                self._insert_bar(ticker, market_data)
            elif isinstance(market_data, QuoteData):
                self._insert_or_update_quote(ticker, market_data)

        self.last_updated = timestamp
        self.event_queue.put(MarketEvent(timestamp=timestamp, data=data))
        self.notify(EventType.MARKET_EVENT)  # update database
        
    def _insert_bar(self, ticker: str, data: MarketData) -> None:
        """
        Inserts or updates bar data for a specific ticker.

        Parameters:
        - ticker (str): The ticker symbol.
        - data (BarData): The bar data to insert or update.
        """
        # Directly insert or update BarData
        self.book[ticker] = data

    def _insert_or_update_quote(self, ticker: str, quote_data: QuoteData) -> None:
        """
        Inserts or updates quote data for a specific ticker.

        Parameters:
        - ticker (str): The ticker symbol.
        - quote_data (QuoteData): The quote data to insert or update.
        """
        self.book[ticker] = quote_data  # For keeping only the most recent quote:

    def current_price(self, ticker: str) -> float:
        """
        Retrieves the current price for a given ticker.

        Parameters:
        - ticker (str): The ticker symbol.

        Returns:
        - float or None: The current price if available, else None.
        """
        if ticker in self.book:
            data = self.book[ticker]
            if self.data_type.value == MarketDataType.BAR.value:
                return float(data.close) # returns close as it is most recent
            elif self.data_type.value == MarketDataType.QUOTE.value: 
                return float((data.ask + data.bid) / 2) # returns a mid-price
        else:
            return None  # Ticker not found

    def current_prices(self) -> dict:
        """
        Retrieves the current prices for all tickers in the book.

        Returns:
        - dict: A dictionary of ticker symbols to their current prices.
        """
        prices = {}
        for key, data in self.book.items():
            if self.data_type.value == MarketDataType.BAR.value:
                prices[key] = float(data.close) # convert Decimal to float
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
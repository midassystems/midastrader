from queue import Queue
from typing import Dict
from midas.engine.events import MarketEvent
from midas.engine.components.observer import Subject, EventType
from mbn import RecordMsg

# import mbn


class OrderBook(Subject):
    """Manages market data updates and notifies observers about market changes."""

    def __init__(self, event_queue: Queue):
        """
        Initializes the order book with a specific market data type and an event queue.

        Parameters:
        - data_type (MarketDataType): The type of data the order book will handle.
        - event_queue (Queue): The event queue to post market events to.
        """
        super().__init__()

        self.event_queue = event_queue
        self.last_updated = None
        self.book: Dict[str, RecordMsg] = {}

    def update(self, record: RecordMsg, ticker: str) -> None:
        """
        Update the market data in the order book and notify observers of market events.

        Parameters:
        - data (Dict[str, Union[BarData, QuoteData]]): The market data to be updated.
        """
        # Update book
        self.book[ticker] = record
        self.last_updated = record.ts_event

        # Put in queue
        self.event_queue.put(MarketEvent(record.ts_event, {ticker: record}))
        self.notify(EventType.MARKET_EVENT)  # update database

    def retrieve_ticker(self, ticker: str) -> RecordMsg:
        """
        Retrieves the current price for a given ticker.

        Parameters:
        - ticker (str): The ticker symbol.

        Returns:
        - float or None: The current price if available, else None.
        """
        # if ticke r in self.book:
        return self.book[ticker]
        # else:
        #     return None  # Ticker not found

    def retrieve_all(self) -> Dict[str, RecordMsg]:
        """
        Retrieves the current prices for all tickers in the book.

        Returns:
        - dict: A dictionary of ticker symbols to their current prices.
        """
        return self.book

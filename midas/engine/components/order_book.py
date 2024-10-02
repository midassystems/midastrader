from typing import Dict
from mbn import RecordMsg
from midas.engine.events import MarketEvent
from midas.utils.logger import SystemLogger
from midas.engine.components.observer.base import Subject, Observer, EventType
from midas.symbol import SymbolMap


class OrderBook(Subject, Observer):
    """Manages market data updates and notifies observers about market changes."""

    def __init__(self, symbol_map: SymbolMap):
        """
        Initializes the order book with a specific market data type and an event queue.

        Parameters:
        - data_type (MarketDataType): The type of data the order book will handle.
        - event_queue (Queue): The event queue to post market events to.
        """
        super().__init__()
        self.symbol_map = symbol_map
        self.logger = SystemLogger.get_logger()
        self.last_updated = None
        self.book: Dict[int, RecordMsg] = {}
        self.tickers_loaded = False  # had data for all tickers

    def check_tickers_loaded(self) -> bool:
        return set(self.symbol_map.instrument_ids) == set(self.book.keys())

    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        record: RecordMsg,
    ) -> None:
        """
        Handles notifications received from other subjects (like DataClient).

        Parameters:
        - subject (Subject): The subject that triggered the event.
        - event_type (EventType): The type of event that was triggered.
        - record (RecordMsg, optional): The market data record.
        - ticker (str, optional): The ticker symbol for the market data.
        """
        if event_type == EventType.MARKET_DATA and record:
            # Update the order book with the new market data
            self.update_book(record)

            # Put market event in the event queue
            market_event = MarketEvent(timestamp=record.ts_event, data=record)
            self.logger.info(market_event)

            # Check inital data loaded
            if not self.tickers_loaded:
                self.tickers_loaded = self.check_tickers_loaded()

            # Notify any observers about the market update
            self.notify(EventType.ORDER_BOOK, market_event)

    def update_book(self, record: RecordMsg) -> None:
        self.book[record.instrument_id] = record
        self.last_updated = record.ts_event

    def retrieve(self, instrument_id: int) -> RecordMsg:
        """
        Retrieves the current price for a given ticker.

        Parameters:
        - ticker (str): The ticker symbol.

        Returns:
        - float or None: The current price if available, else None.
        """
        return self.book[instrument_id]

    def retrieve_all(self) -> Dict[int, RecordMsg]:
        """
        Retrieves the current prices for all tickers in the book.

        Returns:
        - dict: A dictionary of ticker symbols to their current prices.
        """
        return self.book

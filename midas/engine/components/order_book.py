from typing import Dict
from mbn import RecordMsg
from midas.engine.events import MarketEvent
from midas.utils.logger import SystemLogger
from midas.engine.components.observer.base import Subject, Observer, EventType
from midas.symbol import SymbolMap


class OrderBook(Subject, Observer):
    """
    Manages market data updates and notifies observers about market changes.

    The `OrderBook` class maintains the latest market data for instruments, updates the order book
    when new data arrives, and notifies observers about market changes. It also provides methods
    for retrieving market data.
    """

    def __init__(self, symbol_map: SymbolMap):
        """
        Initializes the OrderBook with a symbol map and prepares internal state.

        Args:
            symbol_map (SymbolMap): Mapping of instrument IDs to `Symbol` objects.
        """
        super().__init__()
        self.symbol_map = symbol_map
        self.logger = SystemLogger.get_logger()
        self.book: Dict[int, RecordMsg] = {}
        self.last_updated = None
        self.tickers_loaded = False

    def check_tickers_loaded(self) -> bool:
        """
        Checks if market data for all tickers in the symbol map has been loaded.

        Returns:
            bool: True if data for all tickers is loaded, otherwise False.
        """
        return set(self.symbol_map.instrument_ids) == set(self.book.keys())

    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        record: RecordMsg,
    ) -> None:
        """
        Handles market data events and updates the order book.

        Behavior:
            - Updates the order book with the new market data.
            - Logs the market event.
            - Checks if initial data for all tickers has been loaded.
            - Notifies observers of the updated market state.

        Args:
            subject (Subject): The subject that triggered the event.
            event_type (EventType): The type of event being handled (e.g., `MARKET_DATA`).
            record (RecordMsg): The market data record to process.

        """
        if event_type == EventType.MARKET_DATA and record:
            # Update the order book with the new market data
            self.update_book(record)

            # Put market event in the event queue
            market_event = MarketEvent(timestamp=record.ts_event, data=record)
            self.logger.debug(market_event)

            # Check inital data loaded
            if not self.tickers_loaded:
                self.tickers_loaded = self.check_tickers_loaded()

            # Notify any observers about the market update
            self.notify(EventType.ORDER_BOOK, market_event)

    def update_book(self, record: RecordMsg) -> None:
        """
        Updates the order book with a new market data record.

        Args:
            record (RecordMsg): The market data record to add or update in the order book.
        """
        self.book[record.instrument_id] = record
        self.last_updated = record.ts_event

    def retrieve(self, instrument_id: int) -> RecordMsg:
        """
        Retrieves the market data for a specific instrument.

        Args:
            instrument_id (int): The unique ID of the instrument.

        Returns:
            RecordMsg: The latest market data for the given instrument ID.
        """
        return self.book[instrument_id]

    def retrieve_all(self) -> Dict[int, RecordMsg]:
        """
        Retrieves the market data for all instruments in the order book.

        Returns:
            Dict[int, RecordMsg]: A dictionary mapping instrument IDs to their latest market data.
        """
        return self.book

import queue
import time
from typing import Dict
from mbn import RecordMsg
from threading import Lock
from typing import Optional
import threading

from midastrader.config import Mode
from midastrader.structs.symbol import SymbolMap
from midastrader.structs.events import MarketEvent, EODEvent
from midastrader.message_bus import MessageBus, EventType
from midastrader.structs.events.base import SystemEvent
from midastrader.core.adapters.base import CoreAdapter


class OrderBook:
    """
    Singleton OrderBook for shared access to market data.

    Provides thread-safe read access to components like strategies and brokers,
    and controlled write access via the OrderBookManager.
    """

    _instance: Optional["OrderBook"] = None
    _lock: Lock = Lock()  # Thread-safe singleton initialization

    def __init__(self):
        if OrderBook._instance is not None:
            raise Exception(
                "OrderBook is a singleton. Use get_instance() to access."
            )
        self._book: Dict[int, RecordMsg] = {}
        self._last_updated: int = 0
        self._tickers_loaded = False

        self._write_lock = Lock()  # Lock for controlling write access

    @staticmethod
    def get_instance() -> "OrderBook":
        with OrderBook._lock:
            if OrderBook._instance is None:
                OrderBook._instance = OrderBook()
        return OrderBook._instance

    # Read methods (thread-safe)
    def retrieve(self, instrument_id: int) -> Optional[RecordMsg]:
        """
        Retrieve market data for a specific instrument.
        """
        return self._book.get(instrument_id)

    # Read methods (thread-safe)
    @property
    def last_updated(self) -> int:
        """
        Retrieve market data for a specific instrument.
        """
        return self._last_updated

    @property
    def tickers_loaded(self) -> bool:
        """
        Retrieve market data for a specific instrument.
        """
        return self._tickers_loaded

    def retrieve_all(self) -> Dict[int, RecordMsg]:
        """
        Retrieve market data for all instruments.
        """
        # with self._lock:  # Ensure thread-safe read for a full copy
        return self._book.copy()

    # Methods reserved for OrderBookManager
    def _update(self, record: RecordMsg) -> None:
        """
        Updates the order book with a new market data record.

        Args:
            record (RecordMsg): The market data record to add or update in the order book.
        """
        # Thread-safe in-place update
        with self._write_lock:
            self._book[record.instrument_id] = record
            self._last_updated = record.ts_event


class OrderBookManager(CoreAdapter):
    """
    Manages market data updates and notifies observers about market changes.

    The `OrderBook` class maintains the latest market data for instruments, updates the order book
    when new data arrives, and notifies observers about market changes. It also provides methods
    for retrieving market data.
    """

    def __init__(self, symbols_map: SymbolMap, bus: MessageBus, mode: Mode):
        """
        Initializes the OrderBook with a symbol map and prepares internal state.

        Args:
            symbol_map (SymbolMap): Mapping of instrument IDs to `Symbol` objects.
        """
        super().__init__(symbols_map, bus)
        self.mode = mode
        self.book = OrderBook.get_instance()
        self.running = threading.Event()

        # Subscribe to events
        self.data_queue = self.bus.subscribe(EventType.DATA)
        self.equity_update_flag = self.bus.subscribe(EventType.EQUITY_UPDATED)

    def process(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        self.logger.info("Orderbook running ...")
        self.running.set()

        while not self.shutdown_event.is_set():
            try:
                item = self.data_queue.get()
                # self.logger.info(f"OB - {item}")
                self.handle_event(item)
            except queue.Empty:
                continue

        self.cleanup()

    def cleanup(self) -> None:
        self.logger.info("Shutting down orderbook manager.")

    def handle_event(self, event: SystemEvent) -> None:
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
        if isinstance(event, EODEvent):
            # Publish that EOD processing is complete
            # processed only in backtest situations
            self.bus.publish(EventType.EOD, True)

            while self.bus.get_flag(EventType.EOD):
                continue

            self.bus.publish(EventType.DATA_PROCESSED, True)
            return

        # Update the order book with the new market data
        self.book._update(event)

        # Put market event in the event queue
        market_event = MarketEvent(
            timestamp=event.ts_event,
            data=event,
        )

        # Check inital data loaded
        if not self.book.tickers_loaded:
            self.book._tickers_loaded = self.check_tickers_loaded()

        # Backtest only
        if self.mode == Mode.BACKTEST:
            self.bus.publish(EventType.UPDATE_SYSTEM, True)
            self.bus.publish(EventType.UPDATE_EQUITY, True)

        # Notify any observers about the market update
        self.bus.publish(EventType.ORDER_BOOK, market_event)
        if self.mode == Mode.BACKTEST:
            self.await_updates()

    def check_tickers_loaded(self) -> bool:
        """
        Checks if market data for all tickers in the symbol map has been loaded.

        Returns:
        bool: True if data for all tickers is loaded, otherwise False.
        """
        return set(self.symbols_map.instrument_ids) == set(
            self.book._book.keys()
        )

    def await_updates(self):
        """
        Waits for the EOD_PROCESSED flag to be set.
        """
        self.await_equity_updated()
        self.await_system_updated()
        self.logger.info("Equity & System updated. Proceeding ...")

    def await_equity_updated(self):
        self.logger.info("Waiting for equity updated flag...")
        while True:
            if not self.bus.get_flag(EventType.UPDATE_EQUITY):
                self.logger.info("Equity updated. Proceeding ...")
                time.sleep(0.1)  # Prevent CPU-intensive looping
                break

    def await_system_updated(self):
        self.logger.info("Waiting for system updated flag...")
        while True:
            self.logger.info(
                f"Flag {self.bus.get_flag(EventType.UPDATE_SYSTEM)}"
            )
            if not self.bus.get_flag(EventType.UPDATE_SYSTEM):
                self.logger.info("System updated. Proceeding ...")
                time.sleep(0.1)  # Prevent CPU-intensive looping
                break

import queue
from typing import Dict
from mbn import RecordMsg
from threading import Lock
from typing import Optional

from midastrader.config import Mode
from midastrader.structs.events.rollover_event import RolloverEvent
from midastrader.structs.symbol import SymbolMap
from midastrader.structs.events import MarketEvent, EODEvent
from midastrader.message_bus import MessageBus, EventType

# from midastrader.structs.events.base import SystemEvent
from midastrader.core.adapters.base import CoreAdapter
from midastrader.utils.logger import SystemLogger


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
        self.logger = SystemLogger.get_logger()
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
    def retrieve(self, instrument_id: int) -> RecordMsg:
        """
        Retrieve market data for a specific instrument.
        """
        record = self._book.get(instrument_id)

        if not record:
            self.logger.error(f"RecordMsg not found for {instrument_id}")
            raise RuntimeError("RecordMsg not found for {instrument_id}")

        return record

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
        # self.running = threading.Event()

        # Subscribe to events
        self.data_queue = self.bus.subscribe(EventType.DATA)
        # self.equity_update_flag = self.bus.subscribe(EventType.EQUITY_UPDATED)

    def process(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        self.logger.info("OrderbookManager running ...")
        self.is_running.set()

        while not self.shutdown_event.is_set():
            try:
                item = self.data_queue.get(timeout=0.01)
                if RecordMsg.is_record(item):
                    self.logger.info(f"{type(item)}")
                    self.handle_record(item)
                elif isinstance(item, EODEvent):
                    self.handle_eod(item)
                # elif isinstance(item, RolloverEvent):
                #     self.handle_rollover()
            except queue.Empty:
                continue

        self.cleanup()

    def cleanup(self) -> None:
        while True:
            try:
                item = self.data_queue.get(timeout=1)
                if RecordMsg.is_record(item):  # isinstance(item, RecordMsg):
                    self.handle_record(item)
                elif isinstance(item, EODEvent):
                    self.handle_eod(item)
            except queue.Empty:
                break

        self.logger.info("Shutting down OrderbookManager ...")
        self.is_shutdown.set()

    def handle_eod(self, event: EODEvent) -> None:
        self.logger.debug(event)
        # Publish that EOD processing is complete
        # processed only in backtest situations
        self.bus.publish(EventType.EOD, True)

        while self.bus.get_flag(EventType.EOD):
            continue

        self.bus.publish(EventType.EOD_PROCESSED, True)

    def handle_record(self, record: RecordMsg) -> None:
        if record.rollover_flag == 1:
            self.handle_rollover(record)

        # Update the order book with the new market data
        self.book._update(record)

        # Put market event in the event queue
        market_event = MarketEvent(
            timestamp=record.ts_event,
            data=record,
        )

        self.logger.debug(market_event)

        # Check inital data loaded
        if not self.book.tickers_loaded:
            self.book._tickers_loaded = self.check_tickers_loaded()

        # Backtest only
        # if self.mode == Mode.BACKTEST:

        # Notify any observers about the market update
        # self.bus.publish(EventType.ORDER_BOOK, market_event)

        if self.mode == Mode.BACKTEST:
            self.await_equity_updated()
            self.await_market_data_processed(market_event)
        else:
            self.bus.publish(EventType.ORDER_BOOK, market_event)

    def handle_rollover(self, record: RecordMsg) -> None:
        # if record.rollover_flag == 1:
        id = record.hd.instrument_id
        symbol = self.symbols_map.get_symbol_by_id(id)

        if not symbol:
            raise RuntimeError(f"Symbol not found for instrument_id {id}.")

        old_record = self.book.retrieve(id)

        if not old_record:
            raise RuntimeError(f"Instrument_id {id} not in orderbook.")

        rollover_event = RolloverEvent(
            record.hd.ts_event, symbol, old_record, record
        )

        self.await_rollover_flag(rollover_event)

        # self.book._update(record)

        # self.await_rollover_flag(rollover_event)

    # def handle_event(self, event: ) -> None:
    #     """
    #     Handles market data events and updates the order book.
    #
    #     Behavior:
    #         - Updates the order book with the new market data.
    #         - Logs the market event.
    #         - Checks if initial data for all tickers has been loaded.
    #         - Notifies observers of the updated market state.
    #
    #     Args:
    #         subject (Subject): The subject that triggered the event.
    #         event_type (EventType): The type of event being handled (e.g., `MARKET_DATA`).
    #         record (RecordMsg): The market data record to process.
    #
    #     """
    #     if isinstance(event, EODEvent):
    #         self.logger.debug(event)
    #         # Publish that EOD processing is complete
    #         # processed only in backtest situations
    #         self.bus.publish(EventType.EOD, True)
    #
    #         while self.bus.get_flag(EventType.EOD):
    #             continue
    #
    #         self.bus.publish(EventType.EOD_PROCESSED, True)
    #         return
    #
    #     # if self.mode == Mode.BACKTEST:
    #     #     if event.rollover_flag == 1:
    #     #         rollover_event = RolloverEvent(
    #     #             event.hd.ts_event,
    #     #             self.symbols_map.get_symbol_by_id(event.hd.instrument_id),
    #     #             self.book.retrieve(event.hd.instrument_id),
    #     #             event.close,  # update
    #     #         )
    #     #
    #     #         self.await_rollover_flag(rollover_event)
    #
    #     # Update the order book with the new market data
    #     self.book._update(event)
    #
    #     # Put market event in the event queue
    #     market_event = MarketEvent(
    #         timestamp=event.ts_event,
    #         data=event,
    #     )
    #
    #     self.logger.debug(market_event)
    #
    #     # Check inital data loaded
    #     if not self.book.tickers_loaded:
    #         self.book._tickers_loaded = self.check_tickers_loaded()
    #
    #     # Backtest only
    #     # if self.mode == Mode.BACKTEST:
    #
    #     # Notify any observers about the market update
    #     # self.bus.publish(EventType.ORDER_BOOK, market_event)
    #
    #     if self.mode == Mode.BACKTEST:
    #         self.await_equity_updated()
    #         self.await_market_data_processed(market_event)
    #     else:
    #         self.bus.publish(EventType.ORDER_BOOK, market_event)

    def check_tickers_loaded(self) -> bool:
        """
        Checks if market data for all tickers in the symbol map has been loaded.

        Returns:
        bool: True if data for all tickers is loaded, otherwise False.
        """
        return set(self.symbols_map.instrument_ids) == set(
            self.book._book.keys()
        )

    # def await_updates(self):
    #     """
    #     Waits for the EOD_PROCESSED flag to be set.
    #     """
    #     self.await_equity_updated()
    #     self.await_system_updated()

    def await_rollover_flag(
        self,
        event: RolloverEvent,
    ):
        """
        Signals that the orderbook and by extensions the market has updated so the portoflio
        should be updated to reflect these changes (would be done automatically live).
        """
        self.bus.publish(EventType.ROLLED_OVER, False)
        self.bus.publish(EventType.ROLLOVER_EXITED, False)
        self.bus.publish(EventType.OB_ROLLED, False)
        self.bus.publish(EventType.ROLLOVER, event)

        while True:
            if self.bus.get_flag(EventType.ROLLED_OVER):
                break
            elif self.bus.get_flag(EventType.ROLLOVER_EXITED):
                self.book._update(event.entry_record)
                self.bus.publish(EventType.OB_ROLLED, True)

    def await_equity_updated(self):
        """
        Signals that the orderbook and by extensions the market has updated so the portoflio
        should be updated to reflect these changes (would be done automatically live).
        """
        self.bus.publish(EventType.UPDATE_EQUITY, True)

        while True:
            if not self.bus.get_flag(EventType.UPDATE_EQUITY):
                break

    def await_market_data_processed(self, event: MarketEvent):
        """
        To account for time, this passes orderbook updating until the system
        has had the opportunity to determine if a signal and act on it,
        needed to simulate live gaps between market data events.
        """
        self.bus.publish(EventType.UPDATE_SYSTEM, True)
        self.bus.publish(EventType.ORDER_BOOK, event)

        while True:
            if not self.bus.get_flag(EventType.UPDATE_SYSTEM):
                break

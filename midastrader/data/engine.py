import time
import threading
from enum import Enum
from typing import Dict

from midastrader.message_bus import EventType, MessageBus
from midastrader.structs.symbol import SymbolMap
from midastrader.config import Parameters, Mode
from midastrader.utils.logger import SystemLogger
from midastrader.data.adaptors import HistoricalAdaptor, IBAdaptor


class Vendors(Enum):
    DATABENTO = "databento"
    IB = "interactive_brokers"
    HISTORICAL = "historical"

    @staticmethod
    def from_str(value: str) -> "Vendors":
        match value.lower():
            case "databento":
                return Vendors.DATABENTO
            case "interactive_brokers":
                return Vendors.IB
            case "historical":
                return Vendors.HISTORICAL
            case _:
                raise ValueError(f"Unknown vendor: {value}")

    def adapter(self):
        """Map the enum to the appropriate adapter class."""
        if self == Vendors.IB:
            return IBAdaptor
        elif self == Vendors.HISTORICAL:
            return HistoricalAdaptor
        else:
            raise ValueError(f"No adapter found for vendor: {self.value}")


class DataEngine:
    def __init__(
        self,
        symbols_map: SymbolMap,
        message_bus: MessageBus,
        mode: Mode,
        parameters: Parameters,
    ):
        self.logger = SystemLogger.get_logger()
        self.message_bus = message_bus
        self.parameters = parameters
        self.symbol_map = symbols_map
        self.mode = mode

        self.adapters = {}
        self.threads = []  # List to track threads
        self.completed = threading.Event()  # Event to signal completion
        self.running = threading.Event()

    def initialize_historical(self) -> None:
        self.adapters["historical"].set_mode(self.mode)
        self.adapters["historical"].get_data(self.parameters)

    def construct_adaptors(self, vendors: Dict[str, dict]) -> bool:
        # In Backtest historical is the only vendor in use
        if self.mode == Mode.BACKTEST:
            historical_vendor = {"historical": vendors["historical"]}
            vendors = historical_vendor

        for v in vendors.keys():
            adapter = Vendors.from_str(v).adapter()
            self.adapters[v] = adapter(
                self.symbol_map,
                self.message_bus,
                **vendors[v],
            )

        self.initialize_historical()

        return True

    def start(self):
        """Start adapters in seperate threads."""
        self.logger.info("Data-engine starting ...")

        if self.mode == Mode.BACKTEST:
            self.start_backtest()
        else:
            self.start_live()

        self.logger.info("Data-engine running ...\n")
        self.running.set()

    def start_backtest(self):
        """Start adapters in seperate threads."""
        for adapter in self.adapters.values():
            # Start the threads for each vendor
            thread = threading.Thread(target=adapter.process, daemon=True)
            self.threads.append(thread)
            thread.start()
            adapter.is_running.wait()

        # Start a monitoring thread to check when all adapter threads are done
        threading.Thread(target=self._monitor_threads, daemon=True).start()

    def start_live(self):
        """Start adapters in seperate threads."""
        # Start historical data and load all into the buffer and processes buffer
        historical = self.adapters["historical"]
        historical.process()

        while not self.message_bus.is_queue_empty(EventType.ORDER_BOOK):
            time.sleep(0.1)  # Add a small sleep to avoid busy-waiting

        self.logger.info("Historical data fully processed ...")

        for adapter in self.adapters.values():
            if not isinstance(adapter, HistoricalAdaptor):
                thread = threading.Thread(target=adapter.process, daemon=True)
                self.threads.append(thread)
                thread.start()
                adapter.is_running.wait()

        # Start a monitoring thread to check when all adapter threads are done
        threading.Thread(target=self._monitor_threads, daemon=True).start()

    def _monitor_threads(self):
        """
        Monitor all adapter threads and signal when all are done.
        """
        for thread in self.threads:
            thread.join()  # Wait for each thread to finish

        self.logger.info("DataEngine threads completed, shutting down ...")
        self.completed.set()  # Signal that the DataEngine is done

    def wait_until_complete(self):
        """
        Wait for the engine to complete processing.
        """
        self.completed.wait()

    def stop(self):
        """Start adapters in separate threads."""
        for adapter in self.adapters.values():
            adapter.shutdown_event.set()
            adapter.is_shutdown.wait()

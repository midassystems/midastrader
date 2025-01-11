import threading
from enum import Enum
from typing import Dict

from midastrader.message_bus import MessageBus
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
        if self.mode == Mode.BACKTEST:
            self.start_backtest()
        else:
            self.start_live()

        self.logger.info("Data-engine running ...")
        self.running.set()

    def start_backtest(self):
        """Start adapters in seperate threads."""
        for adapter in self.adapters.values():
            # Start the threads for each vendor
            thread = threading.Thread(target=adapter.process, daemon=True)
            self.threads.append(thread)  # Keep track of threads
            thread.start()
            adapter.running.wait()

        # Start a monitoring thread to check when all adapter threads are done
        threading.Thread(target=self._monitor_threads, daemon=True).start()

    def start_live(self):
        """Start adapters in seperate threads."""
        historical = self.adapters["historical"]
        thread = threading.Thread(target=historical.process, daemon=True)
        self.threads.append(thread)
        thread.start()
        thread.join()  # Hold until historical data loaded

        for adapter in self.adapters.values():
            if not isinstance(adapter, HistoricalAdaptor):
                # Start the threads for each vendor
                thread = threading.Thread(target=adapter.process, daemon=True)
                self.threads.append(thread)  # Keep track of threads
                thread.start()
                adapter.running.wait()

        # Start a monitoring thread to check when all adapter threads are done
        threading.Thread(target=self._monitor_threads, daemon=True).start()

    def _monitor_threads(self):
        """
        Monitor all adapter threads and signal when all are done.
        """
        for thread in self.threads:
            thread.join()  # Wait for each thread to finish

        self.logger.info("Data Engine - All adapter threads have completed.")
        self.completed.set()  # Signal that the DataEngine is done

    def wait_until_complete(self):
        """
        Wait for the engine to complete processing.
        """
        self.completed.wait()  # Block until the completed event is set

    def stop(self):
        """Start adapters in separate threads."""
        for adapter in self.adapters:
            adapter.shutdown_event.set()

        self.logger.info("Shutting down DataEngine...")

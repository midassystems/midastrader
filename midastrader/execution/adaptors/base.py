import threading
from abc import ABC, abstractmethod

from midastrader.message_bus import MessageBus, EventType
from midastrader.structs.symbol import SymbolMap
from midastrader.utils.logger import SystemLogger


class ExecutionAdapter(ABC):
    def __init__(self, symbols_map: SymbolMap, bus: MessageBus):
        self.bus = bus
        self.symbols_map = symbols_map
        self.logger = SystemLogger.get_logger()
        self.shutdown_event = threading.Event()  # Flag to signal shutdown
        self.running = threading.Event()

        self.order_queue = self.bus.subscribe(EventType.ORDER)

    @abstractmethod
    def process(self) -> None:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass

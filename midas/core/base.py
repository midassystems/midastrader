import threading
from abc import ABC, abstractmethod

from midas.message_bus import MessageBus
from midas.structs.symbol import SymbolMap
from midas.utils.logger import SystemLogger


class CoreAdapter(ABC):
    def __init__(self, symbols_map: SymbolMap, bus: MessageBus):
        self.bus = bus
        self.symbols_map = symbols_map
        self.logger = SystemLogger.get_logger()

        # Flag to signal shutdown
        self.shutdown_event = threading.Event()

    @abstractmethod
    def process(self) -> None:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass

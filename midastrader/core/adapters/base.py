import threading
from abc import ABC, abstractmethod

from midastrader.message_bus import MessageBus
from midastrader.structs.symbol import SymbolMap
from midastrader.utils.logger import SystemLogger


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

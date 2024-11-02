import pandas as pd
import importlib.util
from typing import Type
from typing import List
from abc import ABC, abstractmethod
from midas.engine.components.order_book import OrderBook
from midas.signal import SignalInstruction
from midas.engine.components.portfolio_server import PortfolioServer
from midas.engine.events import SignalEvent, MarketEvent
from midas.symbol import SymbolMap
from midas.engine.components.observer.base import Subject, Observer, EventType
from midas.utils.logger import SystemLogger


class BaseStrategy(Subject, Observer, ABC):
    """
    Abstract base class for trading strategies, providing a framework for handling market data,
    generating signals, and managing orders. Designed to be extended with specific strategy implementations.
    """

    def __init__(
        self,
        symbols_map: SymbolMap,
        portfolio_server: PortfolioServer,
        order_book: OrderBook,
    ):
        """
        Initialize the strategy with necessary components for data handling and event management.

        Parameters:
        - portfolio_server (PortfolioServer): The server handling the portfolio operations.
        - order_book (OrderBook): The book that maintains and updates market data.
        - logger (logging.Logger): Logger for recording activity and debugging.
        - event_queue (Queue): Queue for dispatching events like signals and orders.
        """
        super().__init__()
        self.logger = SystemLogger.get_logger()
        self.symbols_map = symbols_map
        self.order_book = order_book
        self.portfolio_server = portfolio_server
        self.historical_data = None

    @abstractmethod
    def prepare(self, hist_data: pd.DataFrame):
        """
        Perform any initial setup required before the strategy can start processing events.
        """
        pass

    @abstractmethod
    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        event: MarketEvent,
    ):
        """
        Handle the event based on the type.

            Parameters:
            - subject (Subject): The subject that triggered the event.
                - event_type (EventType): The type of event that was triggered.
        """
        pass

    @abstractmethod
    def get_strategy_data(self) -> pd.DataFrame:
        """
        Get strategy-specific data.
        """
        pass

    def set_signal(
        self,
        trade_instructions: List[SignalInstruction],
        timestamp: int,
    ):
        """
        Creates and queues a signal event based on the strategy's trade instructions.

        Parameters:
        - trade_instructions (List[SignalInstruction]): Specific trade instructions to execute.
        - timestamp (int): The time at which the signal is generated.
        """
        try:
            signal_event = SignalEvent(timestamp, trade_instructions)
            self.notify(EventType.SIGNAL, signal_event)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to set SignalEvent : {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error setting SignalEvent: {e}")


def load_strategy_class(
    module_path: str,
    class_name: str,
) -> Type[BaseStrategy]:
    """
    Dynamically loads a strategy class from a given module path and class name.
    """
    spec = importlib.util.spec_from_file_location("module.name", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    strategy_class = getattr(module, class_name)
    if not issubclass(strategy_class, BaseStrategy):
        raise ValueError(
            f"Strategy class {class_name} is not a subclass of BaseStrategy."
        )
    return strategy_class

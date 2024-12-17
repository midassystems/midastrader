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
from midas.engine.components.gateways.backtest import DataClient


class BaseStrategy(Subject, Observer, ABC):
    """
    Abstract base class for trading strategies.

    This class provides a framework for processing market data, generating trading signals,
    and interacting with portfolio components. Specific strategies must inherit from
    this class and implement the abstract methods.

    Attributes:
        logger (SystemLogger): Logger for recording activity and debugging.
        symbols_map (SymbolMap): Mapping of instrument symbols to their corresponding data.
        order_book (OrderBook): Maintains and updates market data.
        portfolio_server (PortfolioServer): Handles portfolio operations, including positions and capital.
        hist_data_client (DataClient): Provides access to historical market data.
        historical_data (Any): Placeholder for loaded historical data.
    """

    def __init__(
        self,
        symbols_map: SymbolMap,
        portfolio_server: PortfolioServer,
        order_book: OrderBook,
        hist_data_client: DataClient,
    ):
        """
        Initializes the strategy with required components.

        Args:
            symbols_map (SymbolMap): Mapping of instrument symbols to `Symbol` objects.
            portfolio_server (PortfolioServer): The portfolio server for managing account and positions.
            order_book (OrderBook): The order book that maintains market data.
            hist_data_client (DataClient): Client for accessing historical market data.
        """
        super().__init__()
        self.logger = SystemLogger.get_logger()
        self.symbols_map = symbols_map
        self.order_book = order_book
        self.portfolio_server = portfolio_server
        self.hist_data_client = hist_data_client
        self.historical_data = None

    @abstractmethod
    def primer(self):
        """
        Performs any initial setup required before the strategy processes events.

        This can include data loading, initialization of parameters, or other preparatory tasks.
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
        Handles incoming events and processes them according to the strategy logic.

        Args:
            subject (Subject): The subject that triggered the event.
            event_type (EventType): The type of the event (e.g., `MARKET_DATA`).
            event (MarketEvent): The market event containing data to process.
        """
        pass

    @abstractmethod
    def get_strategy_data(self) -> pd.DataFrame:
        """
        Retrieves strategy-specific data.

        Returns:
            pd.DataFrame: A DataFrame containing relevant strategy-specific data.
        """
        pass

    def set_signal(
        self,
        trade_instructions: List[SignalInstruction],
        timestamp: int,
    ):
        """
        Creates and dispatches a signal event based on trade instructions.

        Args:
            trade_instructions (List[SignalInstruction]): A list of trade instructions to execute.
            timestamp (int): The time at which the signal is generated (in nanoseconds).

        Raises:
            RuntimeError: If signal creation fails due to invalid input or unexpected errors.
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
    Dynamically loads a strategy class from a specified module and class name.

    Args:
        module_path (str): The file path to the module containing the strategy class.
        class_name (str): The name of the strategy class to load.

    Returns:
        Type[BaseStrategy]: The loaded strategy class.

    Raises:
        ValueError: If the specified class is not a subclass of `BaseStrategy`.
        AttributeError: If the class name does not exist in the module.
        ImportError: If the module cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("module.name", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    strategy_class = getattr(module, class_name)

    if not issubclass(strategy_class, BaseStrategy):
        raise ValueError(f"{class_name} must be derived from BaseStrategy.")

    return strategy_class

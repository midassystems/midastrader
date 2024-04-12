from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    This class provides a template for developing various trading strategies,
    handling market data, generating signals, and managing orders.
    """

    def __init__(self):
        """
        Initialize the strategy with necessary parameters and components.

        Parameters:
            symbols_map (Dict[str, Contract]): Mapping of symbol strings to Contract objects.
            event_queue (Queue): Event queue for sending events to other parts of the system.
        """
        self.historical_data = None

    @abstractmethod
    def prepare(self):
        """ Takes care of any initial set up needed. """
        pass
    
    @abstractmethod
    def _entry_signal(self):
        """
        Generate an entry signal based on market data.

        Parameters:
            data (Dict): Market data used for generating the entry signal.
        """
        pass

    @abstractmethod
    def _exit_signal(self):
        """
        Generate an exit signal based on market data.

        Parameters:
            data (Dict): Market data used for generating the exit signal.
        """
        pass

    @abstractmethod
    def _asset_allocation(self):
        """
        Define the asset allocation strategy.
        """
        pass
    
    @abstractmethod
    def generate_signals(self):
        """ For the vectorized backtest."""
        pass
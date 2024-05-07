from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies in a financial trading system.

    This class outlines the necessary structure and functions that all derived trading strategies must implement.\n
    These include initializing strategy-specific parameters, preparing any necessary pre-trade configurations, generating trading signals, and managing asset allocations based on the market data.

    Attributes:
    - historical_data: Storage for historical market data, initially set to None.
    """
    def __init__(self):
        """
        Initializes the BaseStrategy with components for managing historical data.
        """
        self.historical_data = None

    @abstractmethod
    def prepare(self):
        """
        Prepares the trading environment or strategy parameters before the trading starts.

        This method should include any initialization or setup procedures that need to run before the strategy can start processing market data.
        """
        pass
    
    @abstractmethod
    def _entry_signal(self):
        """
        Generates an entry signal based on the provided market data.

        This method should analyze the given data and decide whether it's an optimal moment to enter a trade.
        """
        pass

    @abstractmethod
    def _exit_signal(self):
        """
        Generates an exit signal based on the provided market data.

        This method should analyze the given data and decide whether it's an optimal moment to exit a trade.
        """
        pass

    @abstractmethod
    def _asset_allocation(self):
        """
        Defines the asset allocation strategy based on current market conditions and strategy needs.

        This method should outline how the capital is to be distributed among different assets.
        """
        pass
    
    @abstractmethod
    def generate_signals(self):
        """
        Generates trading signals for a vectorized backtest environment.

        This method should implement the logic to produce entry and exit signals based on vectorized market data.
        """
        pass
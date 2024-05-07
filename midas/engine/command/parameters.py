from datetime import datetime
from typing import List, Literal
from dataclasses import dataclass, field

from midas.shared.symbol import Symbol
from midas.shared.utils.unix import iso_to_unix
from midas.shared.market_data import MarketDataType

@dataclass
class Parameters:
    """
    Holds all configuration parameters necessary for setting up and running a trading strategy.

    This class stores detailed settings such as capital allocation, market data type, and time periods for testing and training.
    It also performs validation to ensure all parameters are correctly specified and logically consistent.

    Attributes:
    - strategy_name (str): The name of the trading strategy.
    - capital (int): The amount of capital allocated for the strategy.Only impacts backtest.
    - data_type (MarketDataType): The type of market data used by the strategy (e.g., BAR, QUOTE).
    - test_start (str): Start date of the testing period in 'YYYY-MM-DD' format.
    - test_end (str): End date of the testing period in 'YYYY-MM-DD' format.
    - missing_values_strategy (Literal['drop', 'fill_forward']): Strategy for handling missing data in the dataset.
    - symbols (List[Symbol]): List of symbols (financial instruments) involved in the trading strategy.
    - train_start (str, optional): Start date of the training period in 'YYYY-MM-DD' format.
    - train_end (str, optional): End date of the training period in 'YYYY-MM-DD' format.
    - benchmark (List[str], optional): List of benchmark ticker symbols for performance comparison.
    - tickers (List[str]): List of ticker symbols derived from the symbols attribute.

    Methods:
    - to_dict(): Converts the parameters instance into a dictionary with key-value pairs, suitable for serialization or passing to other components. 
        Converts date strings to UNIX timestamps where applicable.

    """
    strategy_name: str
    capital: int
    data_type: MarketDataType
    test_start: str 
    test_end: str 
    missing_values_strategy : Literal['drop', 'fill_forward'] = 'fill_forward'
    symbols: List[Symbol] = field(default_factory=list)
    train_end: str = None
    train_start: str = None
    benchmark: List[str] = None
    
    # Derived attribute, not directly passed by the user
    tickers: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Type checks
        if not isinstance(self.strategy_name, str):
            raise TypeError(f"strategy_name must be of type str")
        if not isinstance(self.capital, (int, float)):
            raise TypeError(f"capital must be of type int or float")
        if not isinstance(self.data_type, MarketDataType):
            raise TypeError(f"data_type must be an instance of MarketDataType")
        if not isinstance(self.missing_values_strategy, str):
            raise TypeError(f"missing_values_strategy must be of type str")
        if not isinstance(self.train_start, (str, type(None))):
            raise TypeError(f"train_start must be of type str or None")
        if not isinstance(self.train_end, (str, type(None))):
            raise TypeError(f"train_end must be of type str or None")
        if not isinstance(self.test_start, str):
            raise TypeError(f"test_start must be of type str")
        if not isinstance(self.test_end, str):
            raise TypeError(f"test_end must be of type str")
        if not isinstance(self.symbols, list):
            raise TypeError("'symbols' must be of type list")
        if not all(isinstance(symbol, Symbol) for symbol in self.symbols):
            raise TypeError("All items in 'symbols' must be instances of Symbol")
        if self.benchmark is not None:
            if not isinstance(self.benchmark, list):
                raise TypeError("benchmark must be of type list or None")
            if not all(isinstance(item, str) for item in self.benchmark):
                raise TypeError("All items in 'benchmark' must be of type str")
            
        # Constraint checks
        if self.missing_values_strategy not in ['drop', 'fill_forward']:
            raise ValueError(f"'missing_values_strategy' must be either 'drop' or 'fill_forward'")

        if self.capital <= 0:
            raise ValueError(f"'capital' must be greater than zero")
        
        if self.train_start is not None and self.train_end is not None:
            train_start_date = datetime.strptime(self.train_start, '%Y-%m-%d')
            train_end_date = datetime.strptime(self.train_end, '%Y-%m-%d')
            if train_start_date >= train_end_date:
                raise ValueError(f"'train_start' must be before 'train_end'")
            
        test_start_date = datetime.strptime(self.test_start, '%Y-%m-%d')
        test_end_date = datetime.strptime(self.test_end, '%Y-%m-%d')
        
        if self.train_end is not None:
            train_end_date = datetime.strptime(self.train_end, '%Y-%m-%d')
            if train_end_date >= test_start_date:
                raise ValueError(f"'train_end' must be before 'test_start'")
            
        if test_start_date >= test_end_date:
            raise ValueError(f"'test_start' must be before 'test_end'")
            
        # Populate the tickers list based on the provided symbols
        self.tickers = [symbol.ticker for symbol in self.symbols]

    def to_dict(self):
        return {
            "strategy_name": self.strategy_name, 
            "capital": self.capital, 
            "data_type": self.data_type.value, 
            "train_start": int(iso_to_unix(self.train_start)) if self.train_start else None, 
            "train_end":  int(iso_to_unix(self.train_end)) if self.train_end else None, 
            "test_start": int(iso_to_unix(self.test_start)),
            "test_end": int(iso_to_unix(self.test_end)),
            "tickers": self.tickers, 
            "benchmark": self.benchmark
        }   
    

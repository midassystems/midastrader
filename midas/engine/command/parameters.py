import json
from datetime import datetime
from typing import List, Literal
from midas.shared.symbol import *
from dataclasses import dataclass, field
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
    
    # Derived attribute, not directly passed by the user
    tickers: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Type checks
        if not isinstance(self.strategy_name, str):
            raise TypeError(f"'strategy_name' field must be of type str.")
        if not isinstance(self.capital, (int, float)):
            raise TypeError(f"'capital' field must be of type int or float.")
        if not isinstance(self.data_type, MarketDataType):
            raise TypeError(f"'data_type' field must be an instance of MarketDataType.")
        if not isinstance(self.missing_values_strategy, str):
            raise TypeError(f"'missing_values_strategy' field must be of type str.")
        if not isinstance(self.train_start, (str, type(None))):
            raise TypeError(f"'train_start' field must be of type str or None.")
        if not isinstance(self.train_end, (str, type(None))):
            raise TypeError(f"'train_end' field must be of type str or None.")
        if not isinstance(self.test_start, str):
            raise TypeError(f"'test_start' field must be of type str.")
        if not isinstance(self.test_end, str):
            raise TypeError(f"'test_end' field must be of type str.")
        if not isinstance(self.symbols, list):
            raise TypeError(f"'symbols' field must be of type list.")
        if not all(isinstance(symbol, Symbol) for symbol in self.symbols):
            raise TypeError("All items in 'symbols' field must be instances of Symbol")
            
        # Constraint checks
        if self.missing_values_strategy not in ['drop', 'fill_forward']:
            raise ValueError(f"'missing_values_strategy' field must be in ['drop','fill_forward'].")

        if self.capital <= 0:
            raise ValueError(f"'capital' field must be greater than zero.")
        
        if self.train_start is not None and self.train_end is not None:
            train_start_date = datetime.strptime(self.train_start, '%Y-%m-%d')
            train_end_date = datetime.strptime(self.train_end, '%Y-%m-%d')
            if train_start_date >= train_end_date:
                raise ValueError(f"'train_start' field must be before 'train_end'.")
            
        test_start_date = datetime.strptime(self.test_start, '%Y-%m-%d')
        test_end_date = datetime.strptime(self.test_end, '%Y-%m-%d')
        
        if self.train_end is not None:
            train_end_date = datetime.strptime(self.train_end, '%Y-%m-%d')
            if train_end_date >= test_start_date:
                raise ValueError(f"'train_end' field must be before 'test_start'.")
            
        if test_start_date >= test_end_date:
            raise ValueError(f"'test_start' field must be before 'test_end'.")
            
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
            "tickers": self.tickers
        }   
    
    @classmethod
    def from_file(cls, config_file: str) -> 'Parameters':
        with open(config_file, 'r') as file:
            data = json.load(file)
        
        # Validate data_type
        data_type = cls._validate_data_type(data['data_type'])
        
        # Parse and map symbols
        symbols = cls._parse_symbols(data['symbols'])
        
        # Create and return Parameters instance
        return cls(
            strategy_name=data['strategy_name'],
            capital=data['capital'],
            data_type=data_type,
            test_start=data['test_start'],
            test_end=data['test_end'],
            missing_values_strategy=data['missing_values_strategy'],
            symbols=symbols,
            train_start=data.get('train_start'),
            train_end=data.get('train_end')
        )

    @classmethod
    def _validate_data_type(cls, data_type_str: str) -> MarketDataType:
        if data_type_str not in MarketDataType.__members__:
            raise ValueError(f"Invalid data_type '{data_type_str}' in configuration file. Must be one of {list(MarketDataType.__members__.keys())}.")
        return MarketDataType[data_type_str]
    
    @classmethod
    def _parse_symbols(cls, symbols_data: list) -> List[Symbol]:
        symbols = []
        for symbol_data in symbols_data:
            symbol_type = symbol_data.pop('type')
            symbol_class = cls._get_symbol_class(symbol_type)
            symbol_data = cls._map_symbol_enum_fields(symbol_data)
            symbols.append(symbol_class(**symbol_data))
        return symbols

    @classmethod
    def _get_symbol_class(cls, symbol_type: str):
        symbol_classes = {
            'Equity': Equity,
            'Future': Future,
            'Option': Option,
            'Index': Index
        }
        if symbol_type not in symbol_classes:
            raise ValueError(f"Invalid symbol type '{symbol_type}' in configuration file.")
        return symbol_classes[symbol_type]

    @classmethod
    def _map_symbol_enum_fields(cls, symbol_data: dict) -> dict:
        symbol_data['security_type'] = cls._map_enum(SecurityType, symbol_data['security_type'])
        symbol_data['currency'] = cls._map_enum(Currency, symbol_data['currency'])
        symbol_data['exchange'] = cls._map_enum(Venue, symbol_data['exchange'])
        if 'industry' in symbol_data:
            symbol_data['industry'] = cls._map_enum(Industry, symbol_data['industry'])
        if 'contract_units' in symbol_data:
            symbol_data['contract_units'] = cls._map_enum(ContractUnits, symbol_data['contract_units'])
        if 'option_type' in symbol_data:
            symbol_data['option_type'] = cls._map_enum(Right, symbol_data['option_type'])
        return symbol_data
    
    @staticmethod
    def _map_enum(enum_class, value):
        try:
            return enum_class[value]
        except KeyError:
            raise ValueError(f"Invalid value '{value}' for enum {enum_class.__name__}")

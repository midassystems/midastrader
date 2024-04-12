from abc import ABC
import pandas as pd
from enum import Enum
from typing  import  Dict, Union
from dataclasses import dataclass, field

class MarketDataType(Enum):
    QUOTE = 'QUOTE' 
    BAR = 'BAR'

@dataclass
class MarketData(ABC):
    """Abstract base class for market data types."""
    pass

@dataclass
class QuoteData(MarketData):
    timestamp: Union[int, float]
    ask: float
    ask_size: int
    bid: float
    bid_size: int

    def __post_init__(self):
        # Type checks
        if not isinstance(self.timestamp, (float,int)):
            raise TypeError(f"'timestamp' should be in UNIX format of type float or int, got {type(self.timestamp).__name__}")
        if not isinstance(self.ask, (float,int)):
            raise TypeError(f"'ask' must be of type float or int")
        if not isinstance(self.ask_size, (float, int)):
            raise TypeError(f"'ask_size' must be of type float or int")
        if not isinstance(self.bid, (float,int)):
            raise TypeError(f"'bid' must be of type float or int")
        if not isinstance(self.bid_size, (float,int)):
            raise TypeError(f"'bid_size' must be of type float or int")
        
        # Constraint checks
        if self.ask <= 0:
            raise ValueError(f"'ask' must be greater than zero")
        if self.ask_size <= 0:
            raise ValueError(f"'ask_size' must be greater than zero")
        if self.bid <= 0:
            raise ValueError(f"'bid' must be greater than zero")
        if self.bid_size <= 0:
            raise ValueError(f"'bid_size' must be greater than zero")
        
@dataclass
class BarData(MarketData):
    timestamp : Union[int, float]
    open : float
    high : float
    low : float
    close : float
    volume : float

    def __post_init__(self):
        # Type checks
        if not isinstance(self.timestamp, (float, int)):
            raise TypeError(f"'timestamp' should be in UNIX format of type float or int, got {type(self.timestamp).__name__}")
        if not isinstance(self.open, (float,int)):
            raise TypeError(f"'open' must be of type float or int")
        if not isinstance(self.close, (float, int)):
            raise TypeError(f"'close' must be of type float or int")
        if not isinstance(self.high, (float,int)):
            raise TypeError(f"'high' must be of type float or int")
        if not isinstance(self.low, (float,int)):
            raise TypeError(f"'low' must be of type float or int")
        if not isinstance(self.volume, (float,int)):
            raise TypeError(f"'volume' must be of type float or int")
        
        # Constraint checks
        if self.open <= 0:
            raise ValueError(f"'open' must be greater than zero")
        if self.low <= 0:
            raise ValueError(f"'low' must be greater than zero")
        if self.high <= 0:
            raise ValueError(f"'high' must be greater than zero")
        if self.close <= 0:
            raise ValueError(f"'close' must be greater than zero")
        if self.volume < 0:
            raise ValueError(f"'volume' must be non-negative")
        
    @classmethod
    def from_series(cls, series: pd.Series):
        """Create an instance from a data series."""
        return cls(
            timestamp=series['timestamp'],
            open=series['open'],
            high=series['high'],
            low=series['low'],
            close=series['close'],
            volume=series['volume'],
        )

@dataclass
class MarketEvent:
    """
    Event representing market data updates.
    """
    timestamp : Union[int, float]
    data: Dict[str, MarketData]
    type: str = field(init=False, default='MARKET_DATA')

    def __post_init__(self):
        # Type Check
        if not isinstance(self.timestamp, (float,int)):
            raise TypeError(f"'timestamp' should be in UNIX format of type float or int, got {type(self.timestamp).__name__}")
        if not isinstance(self.data, dict):
            raise TypeError("'data' must be of type dict")
        if not all(isinstance(marketdata, MarketData) and isinstance(key, str) for  key, marketdata in self.data.items()):
            raise TypeError("all keys in 'data' must be of type and all values 'data' must be instances of MarketData")
        
        # Constraint check
        if not self.data:
            raise ValueError("'data' dictionary cannot be empty")


    def __str__(self) -> str:
        string = f"\n{self.type} : \n"
        for contract, market_data in self.data.items():
            string += f" {contract} : {market_data.__dict__}\n"
        return string
    
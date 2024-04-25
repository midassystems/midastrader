import numpy as np
from typing  import Dict
from dataclasses import dataclass, field

from shared.market_data import MarketData

@dataclass
class MarketEvent:
    """
    Represents an event that encapsulates market data updates, triggered when new market data is received.

    This event is fundamental in a trading system for processing live market data updates, informing strategies and
    other components of new market conditions.

    Attributes:
    - timestamp (np.uint64): The UNIX timestamp in nanoseconds when the market data was received.
    - data (Dict[str, MarketData]): A dictionary mapping each contract's identifier to its respective MarketData object.
    - type (str): Automatically set to 'MARKET_DATA', indicating the type of event.
    """
    timestamp : np.uint64
    data: Dict[str, MarketData]
    type: str = field(init=False, default='MARKET_DATA')

    def __post_init__(self):
        # Type Check
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("timestamp must be of type np.uint64.")
        if not isinstance(self.data, dict):
            raise TypeError("'data' must be of type dict")
        if not all(isinstance(marketdata, MarketData) and isinstance(key, str) for  key, marketdata in self.data.items()):
            raise TypeError("all keys in 'data' must be of type str and all values 'data' must be instances of MarketData")
        
        # Constraint check
        if not self.data:
            raise ValueError("'data' dictionary cannot be empty")


    def __str__(self) -> str:
        string = f"\n{self.type} : \n"
        for contract, market_data in self.data.items():
            string += f" {contract} : {market_data.__dict__}\n"
        return string

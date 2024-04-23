# shared/market_data.py
from abc import ABC
import numpy as np
import pandas as pd
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

class MarketDataType(Enum):
    QUOTE = 'QUOTE' 
    BAR = 'BAR'

@dataclass
class MarketData(ABC):
    """Abstract base class for market data types."""
    pass

@dataclass
class BarData(MarketData):
    ticker: str
    timestamp: np.uint64
    open: Decimal
    close: Decimal
    high: Decimal
    low: Decimal
    volume: np.uint64

    def __post_init__(self):
        # Type checks
        if not isinstance(self.ticker, str):
            raise TypeError("ticker must be of type str.")        
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("timestamp must be of type np.uint64.")
        if not isinstance(self.open, Decimal):
            raise TypeError("open must be of type Decimal.")
        if not isinstance(self.high, Decimal):
            raise TypeError("high must be of type Decimal.")
        if not isinstance(self.low, Decimal):
            raise TypeError("low must be of type Decimal.")
        if not isinstance(self.close, Decimal):
            raise TypeError("close must be of type Decimal.")
        if not isinstance(self.volume, np.uint64):
            raise TypeError("volume must be of type np.uint64.")
        

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
        
    # @classmethod
    # def from_series(cls, series: pd.Series):
    #     """Create an instance from a data series."""
    #     return cls(
    #         ticker=series
    #         timestamp=series['timestamp'],
    #         open=series['open'],
    #         high=series['high'],
    #         low=series['low'],
    #         close=series['close'],
    #         volume=series['volume'],
    #     )
    
    def to_dict(self):
        return {
            "symbol": self.ticker,
            "timestamp": int(self.timestamp),
            "open": str(round_decimal(self.open)),
            "close": str(round_decimal(self.close)),
            "high": str(round_decimal(self.high)),
            "low": str(round_decimal(self.low)),
            "volume": int(self.volume)
        }
    
def dataframe_to_bardata(df):
    # Convert the DataFrame to a list of BarData objects
    bardata_list = [
        BarData(
            ticker=row['symbol'],
            timestamp=np.uint64(row.name),  # Assuming row.name is the index and corresponds to 'ts_event'
            open=Decimal(row['open']),
            close=Decimal(row['close']),
            high=Decimal(row['high']),
            low=Decimal(row['low']),
            volume=np.uint64(row['volume'])
        ) for index, row in df.iterrows()
    ]
    return bardata_list

def round_decimal(value):
    return Decimal(value).quantize(Decimal('.0001'), rounding=ROUND_HALF_UP)

@dataclass
class QuoteData(MarketData):
    ticker: str
    timestamp: int
    ask: Decimal
    ask_size: Decimal
    bid: Decimal
    bid_size: Decimal

    def __post_init__(self):
        # Type checks
        if not isinstance(self.ticker, str):
            raise TypeError("ticker must be of type str.")        
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("timestamp must be of type np.uint64.")
        if not isinstance(self.ask, Decimal):
            raise TypeError(f"'ask' must be of type Decimal")
        if not isinstance(self.ask_size, Decimal):
            raise TypeError(f"'ask_size' must be of type Decimal")
        if not isinstance(self.bid, Decimal):
            raise TypeError(f"'bid' must be of type Decimal")
        if not isinstance(self.bid_size, Decimal):
            raise TypeError(f"'bid_size' must be of type Decimal")
        
        # Constraint checks
        if self.ask <= 0:
            raise ValueError(f"'ask' must be greater than zero")
        if self.ask_size <= 0:
            raise ValueError(f"'ask_size' must be greater than zero")
        if self.bid <= 0:
            raise ValueError(f"'bid' must be greater than zero")
        if self.bid_size <= 0:
            raise ValueError(f"'bid_size' must be greater than zero")
        
    def to_dict(self):
        return {
            "ticker": self.ticker,
            "timestamp": self.timestamp,
            "ask": self.ask,
            "ask_size": self.ask_size,
            "bid": self.bid,
            "bid_size": self.bid_size 
        }

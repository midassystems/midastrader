import numpy as np
from abc import ABC
from enum import Enum
from typing import List
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

class MarketDataType(Enum):
    QUOTE = 'QUOTE' 
    BAR = 'BAR'

@dataclass
class MarketData(ABC):
    """Abstract base class for market data types."""
    ticker: str
    timestamp: np.uint64

    def __post_init__(self):
        # Type checks
        if not isinstance(self.ticker, str):
            raise TypeError("'ticker' field must be of type str.")        
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("'timestamp' field must be of type np.uint64.")
        
    def to_dict(self):
        return {
            "symbol": self.ticker,
            "timestamp": int(self.timestamp)}

@dataclass
class BarData(MarketData):
    open: Decimal
    close: Decimal
    high: Decimal
    low: Decimal
    volume: np.uint64

    def __post_init__(self):
        # Type checks
        super().__post_init__()
        if not isinstance(self.open, Decimal):
            raise TypeError("'open' field must be of type Decimal.")
        if not isinstance(self.high, Decimal):
            raise TypeError("'high' field must be of type Decimal.")
        if not isinstance(self.low, Decimal):
            raise TypeError("'low' field must be of type Decimal.")
        if not isinstance(self.close, Decimal):
            raise TypeError("'close' field must be of type Decimal.")
        if not isinstance(self.volume, np.uint64):
            raise TypeError("'volume' field must be of type np.uint64.")

        # Constraint checks
        if self.open <= 0:
            raise ValueError(f"'open' must be greater than zero.")
        if self.low <= 0:
            raise ValueError(f"'low' must be greater than zero.")
        if self.high <= 0:
            raise ValueError(f"'high' must be greater than zero.")
        if self.close <= 0:
            raise ValueError(f"'close' must be greater than zero.")
        if self.volume < 0:
            raise ValueError(f"'volume' must be non-negative.")
    
    def to_dict(self):
        dict = super().to_dict()
        dict["open"]= str(round_decimal(self.open))
        dict["close"]= str(round_decimal(self.close))
        dict["high"]= str(round_decimal(self.high))
        dict["low"]= str(round_decimal(self.low))
        dict["volume"]= int(self.volume)

        return dict
    
def dataframe_to_bardata(df) -> List[BarData]:
    """
    Converts a DataFrame containing OHLCV (Open, High, Low, Close, Volume) data into a list of BarData objects.

    Parameters:
    - df (pd.DataFrame): A pandas DataFrame with columns 'symbol', 'open', 'close', 'high', 'low', and 'volume'. The index of the DataFrame should represent the timestamp of the data.

    Returns:
    - list: A list of BarData objects containing the data from the DataFrame.
    """
    bardata_list = [
        BarData(
            ticker=row['symbol'],
            timestamp=np.uint64(row.name),
            open=Decimal(row['open']),
            close=Decimal(row['close']),
            high=Decimal(row['high']),
            low=Decimal(row['low']),
            volume=np.uint64(row['volume'])
        ) for index, row in df.iterrows()
    ]
    return bardata_list

def round_decimal(value) -> Decimal:
    """
    Rounds a numeric value to four decimal places using standard half-up rounding.

    Parameters:
    - value (float or str or Decimal): The numeric value to be rounded.

    Returns:
    - Decimal: The rounded value as a Decimal object, precise to four decimal places.
    """
    return Decimal(value).quantize(Decimal('.0001'), rounding=ROUND_HALF_UP)

@dataclass
class QuoteData(MarketData):
    ask: Decimal
    ask_size: Decimal
    bid: Decimal
    bid_size: Decimal

    def __post_init__(self):
        # Type checks
        super().__post_init__()
        if not isinstance(self.ask, Decimal):
            raise TypeError(f"'ask' field must be of type Decimal.")
        if not isinstance(self.ask_size, Decimal):
            raise TypeError(f"'ask_size' field must be of type Decimal.")
        if not isinstance(self.bid, Decimal):
            raise TypeError(f"'bid' field must be of type Decimal.")
        if not isinstance(self.bid_size, Decimal):
            raise TypeError(f"'bid_size' field must be of type Decimal.")
        
        # Constraint checks
        if self.ask <= 0:
            raise ValueError(f"'ask' field must be greater than zero.")
        if self.ask_size <= 0:
            raise ValueError(f"'ask_size' field must be greater than zero.")
        if self.bid <= 0:
            raise ValueError(f"'bid' field must be greater than zero.")
        if self.bid_size <= 0:
            raise ValueError(f"'bid_size' field must be greater than zero.")
        
    def to_dict(self):
        dict = super().to_dict()
        dict["ask"] = self.ask
        dict["ask_size"] = self.ask_size
        dict["bid"] = self.bid
        dict["bid_size"] = self.bid_size
        return dict

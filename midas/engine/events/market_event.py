from typing import Union
from mbn import OhlcvMsg, BboMsg
from dataclasses import dataclass, field


@dataclass
class MarketEvent:
    """
    Represents an event that encapsulates market data updates, triggered when new market data is received.

    This event is fundamental in a trading system for processing live market data updates, informing strategies and
    other components of new market conditions.

    Attributes:
    - timestamp (int): The UNIX timestamp in nanoseconds when the market data was received.
    - data (RecordMsg): RecordMsg object.
    - type (str): Automatically set to 'MARKET_DATA', indicating the type of event.
    """

    timestamp: int
    data: Union[OhlcvMsg, BboMsg]
    type: str = field(init=False, default="MARKET_DATA")

    def __post_init__(self):
        # Type Check
        if not isinstance(self.timestamp, int):
            raise TypeError("'timestamp' field must be of type int.")
        if not isinstance(self.data, (OhlcvMsg, BboMsg)):
            raise TypeError("'data' field must be of type OhlcvMsg or BboMsg.")

    def __str__(self) -> str:
        string = f"\n{self.type} : \n"
        string += f"  {self.data.instrument_id} : {self.data}\n"
        return string

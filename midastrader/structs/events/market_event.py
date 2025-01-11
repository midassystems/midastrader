from typing import Union
from mbn import OhlcvMsg, BboMsg
from dataclasses import dataclass, field

from midastrader.structs.events.base import SystemEvent


@dataclass
class MarketEvent(SystemEvent):
    """
    Represents a market data event containing updates for instruments in a trading system.

    A `MarketEvent` encapsulates a specific market data update, such as OHLCV (Open, High, Low, Close, Volume)
    or BBO (Best Bid Offer) messages. It is triggered whenever new market data is received and informs strategies
    or components of changing market conditions.

    Attributes:
        timestamp (int): The UNIX timestamp in nanoseconds indicating when the market data was received.
        data (Union[OhlcvMsg, BboMsg]): Market data message, which can be either OHLCV or BBO.
        type (str): Event type, automatically set to 'MARKET_DATA'.
    """

    timestamp: int
    data: Union[OhlcvMsg, BboMsg]
    type: str = field(init=False, default="MARKET_DATA")

    def __post_init__(self):
        """
        Validates the input fields and ensures logical consistency.

        Raises:
            TypeError: If `timestamp` is not an integer or `data` is not an instance of `OhlcvMsg` or `BboMsg`.
        """
        # Type Check
        if not isinstance(self.timestamp, int):
            raise TypeError("'timestamp' must be of type int.")
        if not isinstance(self.data, (OhlcvMsg, BboMsg)):
            raise TypeError("'data' must be of type OhlcvMsg or BboMsg.")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `MarketEvent`.

        Returns:
            str: A formatted string containing the event type, instrument ID, and market data details.
        """
        string = f"\n{self.type} : \n"
        string += f"  {self.data.instrument_id} : {self.data}\n"
        return string

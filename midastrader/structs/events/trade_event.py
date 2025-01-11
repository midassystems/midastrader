from dataclasses import dataclass, field

from midastrader.structs.trade import Trade
from midastrader.structs.events.base import SystemEvent


@dataclass
class TradeEvent(SystemEvent):
    """
    Represents a trade execution event within a trading system.

    The `ExecutionEvent` class captures the details of a trade execution after an order has been executed.
    It serves as a key event to update portfolios, trigger risk management logic, and generate execution reports.
    This event includes detailed information such as the trade details, the financial contract, and the action performed.

    Attributes:
        timestamp (int): The UNIX timestamp in nanoseconds indicating when the execution occurred.
        trade_details (Trade): The executed trade details, including price, volume, and metrics.
        action (Action): The action type associated with the trade (e.g., BUY, SELL).
        contract (Contract): The contract object describing the financial instrument being traded.
        type (str): Event type, automatically set to 'EXECUTION'.
    """

    trade_id: str
    trade: Trade
    type: str = field(init=False, default="TRADE")

    def __post_init__(self):
        """
        Validates the input fields and ensures their types are consistent.

        Raises:
            TypeError: If any of the attributes are not of the expected type.
        """
        # Type Check
        if not isinstance(self.trade_id, str):
            raise TypeError("'trade_id' must be of type str.")
        if not isinstance(self.trade, Trade):
            raise TypeError("'trade' must be of type Trade instance.")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `ExecutionEvent`.

        Returns:
            str: A formatted string containing execution event details such as timestamp, action,
                 contract, and trade details.
        """
        return (
            f"\n{self.type} EVENT:\n"
            f"  Trade ID: {self.trade_id}\n"
            f"  Trade: {self.trade.to_dict()}\n"
        )


@dataclass
class TradeCommissionEvent(SystemEvent):
    """
    Represents a trade execution event within a trading system.

    The `ExecutionEvent` class captures the details of a trade execution after an order has been executed.
    It serves as a key event to update portfolios, trigger risk management logic, and generate execution reports.
    This event includes detailed information such as the trade details, the financial contract, and the action performed.

    Attributes:
        timestamp (int): The UNIX timestamp in nanoseconds indicating when the execution occurred.
        trade_details (Trade): The executed trade details, including price, volume, and metrics.
        action (Action): The action type associated with the trade (e.g., BUY, SELL).
        contract (Contract): The contract object describing the financial instrument being traded.
        type (str): Event type, automatically set to 'EXECUTION'.
    """

    trade_id: str
    commission: float
    type: str = field(init=False, default="TRADE_COMMISSION")

    def __post_init__(self):
        """
        Validates the input fields and ensures their types are consistent.

        Raises:
            TypeError: If any of the attributes are not of the expected type.
        """
        # Type Check
        if not isinstance(self.trade_id, str):
            raise TypeError("'trade_id' must be of type str.")
        if not isinstance(self.commission, float):
            raise TypeError("'commission' must be of type float.")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `ExecutionEvent`.

        Returns:
            str: A formatted string containing execution event details such as timestamp, action,
                 contract, and trade details.
        """
        return (
            f"\n{self.type} EVENT:\n"
            f"  Trade ID: {self.trade_id}\n"
            f"  Commission: {self.commission}\n"
        )

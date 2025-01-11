from ibapi.contract import Contract
from dataclasses import dataclass, field

from midastrader.structs.orders import Action
from midastrader.structs.trade import Trade
from midastrader.structs.events.base import SystemEvent


@dataclass
class ExecutionEvent(SystemEvent):
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

    timestamp: int
    trade_details: Trade
    action: Action
    contract: Contract
    type: str = field(init=False, default="EXECUTION")

    def __post_init__(self):
        """
        Validates the input fields and ensures their types are consistent.

        Raises:
            TypeError: If any of the attributes are not of the expected type.
        """
        # Type Check
        if not isinstance(self.timestamp, int):
            raise TypeError("'timestamp' must be of type int.")
        if not isinstance(self.action, Action):
            raise TypeError("'action' must be of type Action enum.")
        if not isinstance(self.trade_details, Trade):
            raise TypeError("'trade_details' must be of type Trade instance.")
        if not isinstance(self.contract, Contract):
            raise TypeError("'contract' must be of type Contract instance.")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `ExecutionEvent`.

        Returns:
            str: A formatted string containing execution event details such as timestamp, action,
                 contract, and trade details.
        """
        return (
            f"\n{self.type} EVENT:\n"
            f"  Timestamp: {self.timestamp}\n"
            f"  Action: {self.action}\n"
            f"  Contract: {self.contract}\n"
            f"  Execution Details: {self.trade_details.to_dict()}\n"
        )

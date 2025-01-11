from ibapi.contract import Contract
from dataclasses import dataclass, field

from midastrader.structs.orders import BaseOrder, Action
from midastrader.structs.events.base import SystemEvent


@dataclass
class OrderEvent(SystemEvent):
    """
    Represents an order event within a trading system.

    The `OrderEvent` class encapsulates all details relevant to a specific order at a given time.
    It is used to track and manage order-related activities such as placements, modifications,
    and executions within the system.

    Attributes:
        timestamp (int): The UNIX timestamp in nanoseconds when the order event occurred.
        trade_id (int): Unique identifier for the trade associated with the order.
        leg_id (int): Identifies the specific leg of a multi-leg order.
        action (Action): The action type for the order (e.g., BUY or SELL).
        contract (Contract): The financial contract associated with the order.
        order (BaseOrder): The detailed order object containing specifics like quantity and order type.
        type (str): Event type, automatically set to 'ORDER'.
    """

    timestamp: int
    trade_id: int
    leg_id: int
    action: Action
    contract: Contract
    order: BaseOrder
    type: str = field(init=False, default="ORDER")

    def __post_init__(self):
        """
        Validates the input fields and ensures logical consistency.

        Raises:
            TypeError: If any has an incorrect type.
            ValueError: If `trade_id` or `leg_id` is less than or equal to zero.
        """
        # Type Check
        if not isinstance(self.timestamp, int):
            raise TypeError("'timestamp' must be of type int.")
        if not isinstance(self.trade_id, int):
            raise TypeError("'trade_id' must be of type int.")
        if not isinstance(self.leg_id, int):
            raise TypeError("'leg_id' must be of type int.")
        if not isinstance(self.action, Action):
            raise TypeError("'action' must be of type Action enum.")
        if not isinstance(self.contract, Contract):
            raise TypeError("'contract' must be of type Contract.")
        if not isinstance(self.order, BaseOrder):
            raise TypeError("'order' must be of type BaseOrder.")

        # Value Check
        if self.trade_id <= 0:
            raise ValueError("'trade_id' must be greater than zero.")
        if self.leg_id <= 0:
            raise ValueError("'leg_id' must be greater than zero.")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `OrderEvent`.

        Returns:
            str: A formatted string containing details of the order event.
        """
        return (
            f"\n{self.type} EVENT:\n"
            f"  Timestamp: {self.timestamp}\n"
            f"  Trade ID: {self.trade_id}\n"
            f"  Leg ID: {self.leg_id}\n"
            f"  Action: {self.action}\n"
            f"  Contract: {self.contract}\n"
            f"  Order: {self.order.__dict__}\n"
        )

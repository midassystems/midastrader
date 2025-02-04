from dataclasses import dataclass, field
from typing import List

from midastrader.structs.orders import BaseOrder
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
    orders: List[BaseOrder]
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

        if not isinstance(self.orders, list) or not all(
            isinstance(order, BaseOrder) for order in self.orders
        ):
            raise TypeError("'orders' must be of type List[BaseOrder].")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `OrderEvent`.

        Returns:
            str: A formatted string containing details of the order event.
        """
        order_str = "\n    ".join(str(order) for order in self.orders)
        return (
            f"\n{self.type} EVENT:\n"
            f"  Timestamp: {self.timestamp}\n"
            f"  Orders:\n    {order_str}\n"
        )

from dataclasses import dataclass, field

from midastrader.structs.orders import BaseOrder, Action
from midastrader.structs.events.base import SystemEvent
from midastrader.structs.symbol import Symbol


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
    signal_id: int
    action: Action
    symbol: Symbol
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
        if not isinstance(self.signal_id, int):
            raise TypeError("'signal_id' must be of type int.")
        if not isinstance(self.action, Action):
            raise TypeError("'action' must be of type Action enum.")
        if not isinstance(self.symbol, Symbol):
            raise TypeError("'symbol' must be of type Symbol.")
        if not isinstance(self.order, BaseOrder):
            raise TypeError("'order' must be of type BaseOrder.")

        # Value Check
        if self.signal_id <= 0:
            raise ValueError("'signal_id' must be greater than zero.")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `OrderEvent`.

        Returns:
            str: A formatted string containing details of the order event.
        """
        return (
            f"\n{self.type} EVENT:\n"
            f"  Timestamp: {self.timestamp}\n"
            f"  Signal ID: {self.signal_id}\n"
            f"  Action: {self.action}\n"
            f"  Symbol: {self.symbol.midas_ticker}\n"
            f"  Order: {self.order.__dict__}\n"
        )

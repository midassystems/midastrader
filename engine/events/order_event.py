import numpy as np
from ibapi.contract import Contract
from dataclasses import dataclass, field

from shared.orders import BaseOrder, Action

@dataclass
class OrderEvent:
    """
    Represents an order-related event in a trading system, typically triggered when an order is placed, modified, or executed.

    This class is essential for order management within the system, capturing all relevant details about an order at the time of the event. 
    It helps in tracking the lifecycle of trades and ensuring the system responds appropriately to changes in order status.

    Attributes:
    - timestamp (np.uint64): The UNIX timestamp in nanoseconds when the order event occurred.
    - trade_id (int): A unique identifier for the trade associated with this order.
    - leg_id (int): Identifies the specific leg of a multi-leg order.
    - action (Action): The type of action (e.g., BUY, SELL) associated with the order.
    - contract (Contract): The financial contract associated with the order.
    - order (BaseOrder): The order object detailing specifics like order type and quantity.
    - type (str): Automatically set to 'ORDER', denoting the event type.
    """
    timestamp: np.uint64
    trade_id: int
    leg_id: int
    action: Action
    contract: Contract 
    order: BaseOrder  
    type: str = field(init=False, default='ORDER')

    def __post_init__(self):
        # Type Check 
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("timestamp must be of type np.uint64.")
        if not isinstance(self.trade_id, int) or self.trade_id <= 0:
            raise ValueError("'trade_id' must be a non-negative integer.")
        if not isinstance(self.leg_id, int) or self.leg_id <= 0:
            raise ValueError("'leg_id' must be a non-negative integer.")
        if not isinstance(self.action, Action):
            raise TypeError("'action' must be of type Action enum.")
        if not isinstance(self.contract, Contract):
            raise TypeError("'contract' must be of type Contract.")
        if not isinstance(self.order, BaseOrder):
            raise TypeError("'order' must be of type BaseOrder.")

    def __str__(self) -> str:
        string = f"\n{self.type} : \n Timestamp: {self.timestamp}\n Trade ID: {self.trade_id}\n Leg ID: {self.leg_id}\n Action: {self.action}\n Contract: {self.contract}\n Order: {self.order.__dict__}\n"
        return string
    
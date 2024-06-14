import numpy as np
from ibapi.contract import Contract
from dataclasses import dataclass, field
from midas.shared.orders import BaseOrder, Action

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
            raise TypeError("'timestamp' field must be of type np.uint64.")
        if not isinstance(self.trade_id, int):
            raise TypeError("'trade_id' field must be of type int.")
        if not isinstance(self.leg_id, int):
            raise TypeError("'leg_id' field must be of type int.")
        if not isinstance(self.action, Action):
            raise TypeError("'action' field must be of type Action enum.")
        if not isinstance(self.contract, Contract):
            raise TypeError("'contract' field must be of type Contract.")
        if not isinstance(self.order, BaseOrder):
            raise TypeError("'order' field must be of type BaseOrder.")
        
        # Value Check
        if self.trade_id <= 0:
            raise ValueError("'trade_id' field must be greater than zero.")
        if self.leg_id <= 0:
            raise ValueError("'leg_id' field must be greater than zero.")

    def __str__(self) -> str:
        return (
            f"\n{self.type} EVENT:\n"  
            f"  Timestamp: {self.timestamp}\n"  
            f"  Trade ID: {self.trade_id}\n"  
            f"  Leg ID: {self.leg_id}\n"  
            f"  Action: {self.action}\n"  
            f"  Contract: {self.contract}\n"
            f"  Order: {self.order.__dict__}\n"
        )
    
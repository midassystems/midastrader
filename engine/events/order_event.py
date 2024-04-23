import numpy as np
from typing  import  Any, Union
from ibapi.contract import Contract
from dataclasses import dataclass, field

from shared.orders import BaseOrder, Action

@dataclass
class OrderEvent:
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
    
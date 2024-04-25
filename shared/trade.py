import numpy as np
from dataclasses import dataclass
from typing import TypedDict, Union

from shared.utils import unix_to_iso

class ExecutionDetails(TypedDict):
    timestamp: np.uint64
    trade_id: int
    leg_id: int
    symbol: str
    quantity: int
    price: float
    cost: float
    action: str
    fees: float

@dataclass
class Trade:
    trade_id: int
    leg_id: int
    timestamp: np.uint64
    ticker: str
    quantity: Union[int,float]
    price: float
    cost: float
    action: str # BUY/SELL
    fees: float

    def __post_init__(self):
        # Type Validation
        if not isinstance(self.trade_id, int):
            raise TypeError(f"'trade_id' must be of type int")
        if not isinstance(self.leg_id, int):
            raise TypeError(f"'leg_id' must be of type int")
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("timestamp must be of type np.uint64.")
        if not isinstance(self.ticker, str):
            raise TypeError(f"'ticker' must be of type str")
        if not isinstance(self.quantity, (float, int)):
            raise TypeError(f"'quantity' must be of type float or int")
        if not isinstance(self.price, (float, int)):
            raise TypeError(f"'price' must be of type float or int")
        if not isinstance(self.cost, (float, int)):
            raise TypeError(f"'cost' must be of type float or int")
        if not isinstance(self.action, str):
            raise TypeError(f"'action' must be of type str")
        if not isinstance(self.fees, (float, int)):
            raise TypeError(f"'fees' must be of type float or int")
        
        # Constraint Validation
        if self.action not in ['BUY', 'SELL', 'LONG', 'SHORT', 'COVER']:
            raise ValueError(f"'action' must be either 'BUY', 'SELL', 'LONG', 'SHORT', 'COVER'")
        if self.price <= 0:
            raise ValueError(f"'price' must be greater than zero")
        
        #TODO : Add validation for cost/quantity depending on the action

    def __str__(self) -> str:
        return (f"Timestamp: {unix_to_iso(self.timestamp)}\n  Trade ID: {self.trade_id}\n  Leg ID: {self.leg_id}\n  Ticker: {self.ticker}\n  Quantity: {self.quantity}\n  Price: {self.price}\n  Cost: {self.cost}\n  Action: {self.action}\n  Fees: {self.fees}\n")
    
    def __eq__(self, other):
        if not isinstance(other, Trade):
            return NotImplemented
        return self.trade_id == other.trade_id and self.leg_id == other.leg_id
    
    def to_dict(self):
        return {
            "timestamp": int(self.timestamp), 
            "trade_id": self.trade_id,
            "leg_id": self.leg_id,
            "ticker": self.ticker, 
            "quantity": self.quantity,
            "price": self.price, 
            "cost": self.cost,
            "action": self.action, 
            "fees": self.fees
        }

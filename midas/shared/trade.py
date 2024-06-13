import numpy as np
from dataclasses import dataclass
from typing import TypedDict, Union
from midas.shared.utils import unix_to_iso

class ExecutionDetails(TypedDict):
    timestamp: np.uint64
    trade_id: int
    leg_id: int
    symbol: str
    quantity: int
    avg_price: float
    trade_value: float
    action: str
    fees: float

@dataclass
class Trade:
    trade_id: int
    leg_id: int
    timestamp: np.uint64
    ticker: str
    quantity: Union[int,float]
    avg_price: float
    trade_value: float
    action: str # BUY/SELL
    fees: float

    def __post_init__(self):
        # Type Check
        if not isinstance(self.trade_id, int):
            raise TypeError(f"'trade_id' field must be of type int.")
        if not isinstance(self.leg_id, int):
            raise TypeError(f"'leg_id' field must be of type int.")
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError(f"'timestamp' field must be of type np.uint64.")
        if not isinstance(self.ticker, str):
            raise TypeError(f"'ticker' field must be of type str.")
        if not isinstance(self.quantity, (float, int)):
            raise TypeError(f"'quantity' field must be of type float or int.")
        if not isinstance(self.avg_price, (float, int)):
            raise TypeError(f"'avg_price' field must be of type float or int.")
        if not isinstance(self.trade_value, (float, int)):
            raise TypeError(f"'trade_value' field must be of type float or int.")
        # if not isinstance(self.notional_value, (float, int)):
        #     raise TypeError(f"'notional_value' field must be of type float or int.")
        # if not isinstance(self.initial_cost, (float, int)):
        #     raise TypeError(f"'initial_cost' field must be of type float or int.")
        if not isinstance(self.action, str):
            raise TypeError(f"'action' field must be of type str.")
        if not isinstance(self.fees, (float, int)):
            raise TypeError(f"'fees' field must be of type float or int.")
        
        # Value Constraint 
        if self.action not in ['BUY', 'SELL', 'LONG', 'SHORT', 'COVER']:
            raise ValueError(f"'action' field must be in ['BUY', 'SELL', 'LONG', 'SHORT', 'COVER'].")
        if self.avg_price <= 0:
            raise ValueError(f"'avg_price' field must be greater than zero.")

    def __str__(self) -> str:
        return (
            f"Timestamp: {unix_to_iso(self.timestamp)}\n"  
            f"Trade ID: {self.trade_id}\n"  
            f"Leg ID: {self.leg_id}\n"  
            f"Ticker: {self.ticker}\n"  
            f"Quantity: {self.quantity}\n"  
            f"Avg Price: {self.avg_price}\n"  
            f"Trade Value: {self.trade_value}\n"  
            f"Action: {self.action}\n" 
            f"Fees: {self.fees}\n"
        )
    
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
            "avg_price": self.avg_price, 
            "trade_value": self.trade_value,
            "action": self.action, 
            "fees": self.fees
        }

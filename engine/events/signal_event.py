from typing import List, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field
from .order_event import OrderType, Action

@dataclass
class TradeInstruction:
    ticker: str
    order_type: OrderType
    action: Action
    trade_id: int
    leg_id: int
    weight: float

    def __post_init__(self):
        self._data_validation()

    def _data_validation(self):
        if not self.ticker or not isinstance(self.ticker, str):
            raise ValueError("'ticker' must be a non-empty string.")
        
        if not isinstance(self.order_type, OrderType):
            raise ValueError("'order_type' must be of type OrderType enum.")
        
        if not isinstance(self.action, Action):
            raise ValueError("'action' must be of type Action enum.")
        
        if not isinstance(self.trade_id, int) or self.trade_id <= 0:
            raise ValueError("'trade_id' must be a non-negative integer.")
        
        if not isinstance(self.leg_id, int) or self.leg_id <= 0:
            raise ValueError("'leg_id' must be a non-negative integer.")

    def to_dict(self):
        return {
            "ticker": self.ticker,
            "order_type": self.order_type.value,
            "action": self.action.value,
            "trade_id": self.trade_id,
            "leg_id": self.leg_id,
            "weight": round(self.weight,4)
        }

    def __str__(self) -> str:
        return (
            f"Ticker: {self.ticker}, "
            f"Order Type: {self.order_type.name}, "
            f"Action: {self.action.name}, "
            f"Trade ID: {self.trade_id}, "
            f"Leg ID: {self.leg_id}, "
            f"Weight: {self.weight}"
        )
    
class SignalEvent:
    def __init__(self, timestamp: Union[int, float], trade_capital:Union[int, float], trade_instructions: List[TradeInstruction]):
        self.timestamp = timestamp
        self.trade_capital = trade_capital
        self.trade_instructions = trade_instructions
        self._type = 'SIGNAL'
        
        # Type Check 
        if not isinstance(self.timestamp, (float,int)):
            raise TypeError(f"'timestamp' should be in UNIX format of type float or int, got {type(self.timestamp).__name__}")
        if not isinstance(trade_instructions, list):
            raise TypeError(f"'trade_instructions' must be of type list.")
        if not isinstance(self.trade_capital, (float,int)):
            raise TypeError(f"'trade_capital' must be of type float or int.")
        if not all(isinstance(instruction, TradeInstruction) for instruction in self.trade_instructions):
            raise TypeError("All trade instructions must be instances of TradeInstruction.")
        
        # Constraint Check
        if trade_capital <= 0:
            raise ValueError("'trade_capital' must be greater than zero.")
        if len(trade_instructions) == 0:
            raise ValueError("Trade instructions list cannot be empty.")
        
    def __str__(self) -> str:
        instructions_str = "\n  ".join(str(instruction) for instruction in self.trade_instructions)
        return f"\n{self._type} Event: \n Timestamp: {self.timestamp}\n Trade Instructions:\n{instructions_str}"
    
    def to_dict(self):
        return {
            "timestamp": datetime.fromtimestamp(self.timestamp, timezone.utc).isoformat(),
            "trade_instructions": [trade.to_dict() for trade in self.trade_instructions]
        }

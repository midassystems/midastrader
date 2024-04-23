import numpy as np
from typing import List, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field

from shared.signal import TradeInstruction
from shared.utils import unix_to_iso

class SignalEvent:
    def __init__(self, timestamp: np.uint64, trade_capital:Union[int, float], trade_instructions: List[TradeInstruction]):
        self.timestamp = timestamp
        self.trade_capital = trade_capital
        self.trade_instructions = trade_instructions
        self._type = 'SIGNAL'
        
        # Type Check 
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("timestamp must be of type np.uint64.")
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
        iso_timestamp=unix_to_iso(self.timestamp, "US/Eastern")
        return f"\n{self._type} Event: \n Timestamp: {iso_timestamp}\n Trade Instructions:\n{instructions_str}"
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "trade_instructions": [trade.to_dict() for trade in self.trade_instructions]
        }

import numpy as np
from typing import List, Union
from dataclasses import dataclass, field

from midas.shared.utils import unix_to_iso
from midas.shared.signal import TradeInstruction

@dataclass
class SignalEvent:
    """
    Represents a trading signal event, which includes one or more trading instructions based on strategy analysis.

    This event is critical in algorithmic trading as it triggers actions based on the interpretation of market data.
    It includes details such as the timestamp of the signal, the capital allocated for the trade, and a list of specific
    trading instructions that should be executed.

    Attributes:
    - timestamp (np.uint64): The UNIX timestamp in nanoseconds when the signal was generated.
    - trade_capital (Union[int, float]): The amount of capital allocated for executing the trade.
    - trade_instructions (List[TradeInstruction]): A list of detailed trade instructions.
    - type (str): A string identifier for the event type, set to 'SIGNAL'.
    """
    timestamp: np.uint64
    trade_capital: Union[int, float]
    trade_instructions: List[TradeInstruction]
    type: str = field(init=False, default='SIGNAL')

    def __post_init__(self):
        # Type Check 
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("timestamp must be of type np.uint64.")
        if not isinstance(self.trade_instructions, list):
            raise TypeError(f"'trade_instructions' must be of type list.")
        if not isinstance(self.trade_capital, (float,int)):
            raise TypeError(f"'trade_capital' must be of type float or int.")
        if not all(isinstance(instruction, TradeInstruction) for instruction in self.trade_instructions):
            raise TypeError("All trade instructions must be instances of TradeInstruction.")
        
        # Constraint Check
        if self.trade_capital <= 0:
            raise ValueError("'trade_capital' must be greater than zero.")
        if len(self.trade_instructions) == 0:
            raise ValueError("Trade instructions list cannot be empty.")
        
    def __str__(self) -> str:
        instructions_str = "\n  ".join(str(instruction) for instruction in self.trade_instructions)
        iso_timestamp=unix_to_iso(self.timestamp, "US/Eastern")
        return f"\n{self.type} Event: \n Timestamp: {iso_timestamp}\n Trade Instructions:\n{instructions_str}"
    
    def to_dict(self):
        return {
            "timestamp": int(self.timestamp),
            "trade_instructions": [trade.to_dict() for trade in self.trade_instructions]
        }

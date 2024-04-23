import numpy as np
from ibapi.contract import Contract
from typing  import  Dict, Any, Union
from dataclasses import dataclass, field

from shared.orders import Action
from shared.trade import ExecutionDetails

@dataclass
class ExecutionEvent:
    timestamp: np.uint64
    trade_details: ExecutionDetails
    action: Action 
    contract: Contract
    type: str = field(init=False, default='EXECUTION')

    def __post_init__(self):
        # Type Check
        if not isinstance(self.timestamp, np.uint64):
            raise TypeError("timestamp must be of type np.uint64.")
        if not isinstance(self.action, Action):
            raise TypeError("'action' must be of type Action enum.")
        if not isinstance(self.trade_details, dict):
            raise TypeError("'trade_details' must be of type ExecutionDetails dict.")
        if not isinstance(self.contract, Contract):
            raise TypeError("'contract' must be of type Contract instance.")

    def __str__(self) -> str:
        string = f"\n{self.type} : \n Timestamp: {self.timestamp}\n Action: {self.action}\n Contract: {self.contract}\n Execution Details: {self.trade_details}\n"
        return string

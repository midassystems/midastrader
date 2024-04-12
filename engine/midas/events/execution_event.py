from datetime import datetime
from ibapi.contract import Contract
from dataclasses import dataclass, field
from typing  import  Dict, Any, Union, TypedDict

from midas.events import Action
from midas.account_data import Trade
class ExecutionDetails(TypedDict):
    timestamp: Union[int,float]
    trade_id: int
    leg_id: int
    symbol: str
    quantity: int
    price: float
    cost: float
    action: str
    fees: float

@dataclass
class ExecutionEvent:
    timestamp: Union[int, float]
    trade_details: ExecutionDetails
    action: Action 
    contract: Contract
    type: str = field(init=False, default='EXECUTION')

    def __post_init__(self):
        # Type Check
        if not isinstance(self.timestamp, (float,int)):
            raise TypeError(f"'timestamp' should be in UNIX format of type float or int, got {type(self.timestamp).__name__}")
        if not isinstance(self.action, Action):
            raise TypeError("'action' must be of type Action enum.")
        if not isinstance(self.trade_details, dict):
            raise TypeError("'trade_details' must be of type ExecutionDetails dict.")
        if not isinstance(self.contract, Contract):
            raise TypeError("'contract' must be of type Contract instance.")

    def __str__(self) -> str:
        string = f"\n{self.type} : \n Timestamp: {self.timestamp}\n Action: {self.action}\n Contract: {self.contract}\n Execution Details: {self.trade_details}\n"
        return string

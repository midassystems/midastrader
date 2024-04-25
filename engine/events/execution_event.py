import numpy as np
from ibapi.contract import Contract
from dataclasses import dataclass, field

from shared.orders import Action
from shared.trade import ExecutionDetails

@dataclass
class ExecutionEvent:
    """
    Represents an event triggered after the execution of a trade order in a trading system, capturing the
    details of the trade execution.

    This event is vital for tracking trade executions, allowing the system to update portfolios, execute risk management
    protocols, and provide transaction reports. It includes detailed information about the trade, the involved contract,
    and the type of action performed.

    Attributes:
    - timestamp (np.uint64): The UNIX timestamp in nanoseconds when the execution occurred.
    - trade_details (ExecutionDetails): A dictionary or an object detailing the execution of the trade, including price, volume, and other relevant metrics.
    - action (Action): The type of action (e.g., BUY, SELL) that was executed.
    - contract (Contract): The contract object detailing the financial instrument involved in the trade.
    - type (str): The type of the event, set to 'EXECUTION' by default.
    """
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

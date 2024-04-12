from datetime import datetime
from dataclasses import dataclass, field
from typing  import  Dict, Any, Union, TypedDict

@dataclass
class EODEvent:
    timestamp: Union[int, float]
    type: str = field(init=False, default='End-of-day')

    # def __post_init__(self):
    #     # Type Check
    #     # if not isinstance(self.timestamp, (float,int)):
    #     #     raise TypeError(f"'timestamp' should be in UNIX format of type float or int, got {type(self.timestamp).__name__}")

    # def __str__(self) -> str:
    #     string = f"\n{self.type} : \n Timestamp: {self.timestamp}\n Action: {self.action}\n Contract: {self.contract}\n Execution Details: {self.trade_details}\n"
    #     return string

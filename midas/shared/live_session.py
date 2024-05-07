# shared/live_session.py
from dataclasses import dataclass, field

@dataclass
class LiveTradingSession:
    parameters: dict = field(default_factory=dict)
    signal_data: list = field(default_factory=list)
    trade_data: list = field(default_factory=list)
    account_data: list = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dictionary")
        if not all(isinstance(item, dict) for item in self.trade_data):
            raise ValueError("trade_data must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in self.account_data):
            raise ValueError("account_data must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in self.signal_data):
            raise ValueError("signal_data must be a list of dictionaries")
        
    def to_dict(self):
        return {
            "parameters": self.parameters,
            "signals": self.signal_data,
            "trades": self.trade_data,
            "account_data": self.account_data,
        }
    
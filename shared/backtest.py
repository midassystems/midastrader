# shared/backtest.py
from dataclasses import dataclass, field

@dataclass
class Backtest:
    parameters: dict = field(default_factory=dict)
    signal_data: list = field(default_factory=list)
    trade_data: list = field(default_factory=list)
    static_stats: list = field(default_factory=list)
    regression_stats: list = field(default_factory=list)
    timeseries_stats: list = field(default_factory=list)
        
    def __post_init__(self):
        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dictionary")
        if not all(isinstance(item, dict) for item in self.static_stats):
            raise ValueError("static_stats must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in self.regression_stats):
            raise ValueError("regression_stats must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in self.timeseries_stats):
            raise ValueError("timeseries_stats must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in self.trade_data):
            raise ValueError("trade_data must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in self.signal_data):
            raise ValueError("signal_data must be a list of dictionaries")
        
    def to_dict(self):
        return {
            "parameters": self.parameters,
            "static_stats": self.static_stats,
            "regression_stats": self.regression_stats,
            "timeseries_stats":self.timeseries_stats,
            "signals": self.signal_data,
            "trades": self.trade_data,
        }
    
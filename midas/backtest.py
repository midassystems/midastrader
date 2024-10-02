from dataclasses import dataclass, field


@dataclass
class Backtest:
    name: str
    parameters: dict = field(default_factory=dict)
    signal_data: list = field(default_factory=list)
    trade_data: list = field(default_factory=list)
    static_stats: dict = field(default_factory=dict)
    daily_timeseries_stats: list = field(default_factory=list)
    period_timeseries_stats: list = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.parameters, dict):
            raise ValueError("'parameters' field must be a dictionary.")
        if not isinstance(self.static_stats, dict):
            raise ValueError("'static_stats' field must be a dictionaries.")
        if not all(isinstance(item, dict) for item in self.trade_data):
            raise ValueError(
                "'trade_data' field must be a list of dictionaries."
            )
        if not all(isinstance(item, dict) for item in self.signal_data):
            raise ValueError(
                "'signal_data' field must be a list of dictionaries."
            )
        if not all(
            isinstance(item, dict) for item in self.daily_timeseries_stats
        ):
            raise ValueError(
                "'daily_timeseries_stats' field must be a list of dictionaries."
            )
        if not all(
            isinstance(item, dict) for item in self.period_timeseries_stats
        ):
            raise ValueError(
                "'period_timeseries_stats' field must be a list of dictionaries."
            )

    def to_dict(self):
        return {
            "backtest_name": self.name,
            "parameters": self.parameters,
            "static_stats": self.static_stats,
            "daily_timeseries_stats": self.daily_timeseries_stats,
            "period_timeseries_stats": self.period_timeseries_stats,
            "signals": self.signal_data,
            "trades": self.trade_data,
        }

import toml
from enum import Enum
from typing import List
from dataclasses import dataclass, field
from midas.utils.unix import iso_to_unix
from midas.symbol import Symbol, SymbolFactory
from mbn import Schema
from datetime import datetime
from mbn import Parameters as MbnParameters


class Mode(Enum):
    LIVE = "LIVE"
    BACKTEST = "BACKTEST"


class LiveDataType(Enum):
    TICK = "TICK"
    BAR = "BAR"


class Config:
    def __init__(self, config_dict: dict):
        """
        Unified Config class that holds all configuration data.

        Parameters:
        - config_dict (dict): Dictionary representation of the loaded TOML configuration.
        """
        self.general = config_dict.get("general", {})
        self.database = config_dict.get("database", {})
        self.strategy = config_dict.get("strategy", {})
        self.risk = config_dict.get("risk", {})
        self.broker = config_dict.get("broker", {})
        self.data_source = config_dict.get("data_source", {})

        # General settings
        self.session_id = self.general.get("session_id")
        self.mode = Mode[self.general.get("mode").upper()]
        self.log_level = self.general.get("log_level", "INFO")
        self.log_output = self.general.get("log_output", "file")
        self.output_path = self.general.get("output_path", "")
        self.train_data_file = self.general.get("train_data_file", "")
        self.test_data_file = self.general.get("test_data_file", "")

        # Database settings
        self.database_url = self.database.get("url")
        self.database_key = self.database.get("key")

        # Strategy settings
        self.strategy_module = self.strategy.get("logic", {}).get("module")
        self.strategy_class = self.strategy.get("logic", {}).get("class")
        self.strategy_parameters = self.strategy.get("parameters", {})
        self.strategy_parameters["symbols"] = list(
            self.strategy.get("symbols").values()
        )

        # Risk settings
        self.risk_module = self.risk.get("module")
        self.risk_class = self.risk.get("class")

    @classmethod
    def from_toml(cls, config_path: str) -> "Config":
        """
        Load the configuration from a TOML file and return a Config object.
        """
        with open(config_path, "r") as f:
            config_dict = toml.load(f)
        return cls(config_dict)


@dataclass
class Parameters:
    """
    Holds all configuration parameters necessary for setting up and running a trading strategy.

    This class stores detailed settings such as capital allocation, market data type, and time periods for testing and training.
    It also performs validation to ensure all parameters are correctly specified and logically consistent.

    Attributes:
    - strategy_name (str): The name of the trading strategy.
    - capital (int): The amount of capital allocated for the strategy.Only impacts backtest.
    - data_type (MarketDataType): The type of market data used by the strategy (e.g., BAR, QUOTE).
    - test_start (str): Start date of the testing period in 'YYYY-MM-DD' format.
    - test_end (str): End date of the testing period in 'YYYY-MM-DD' format.
    - missing_values_strategy (Literal['drop', 'fill_forward']): Strategy for handling missing data in the dataset.
    - symbols (List[Symbol]): List of symbols (financial instruments) involved in the trading strategy.
    - train_start (str, optional): Start date of the training period in 'YYYY-MM-DD' format.
    - train_end (str, optional): End date of the training period in 'YYYY-MM-DD' format.
    - tickers (List[str]): List of ticker symbols derived from the symbols attribute.

    Methods:
    - to_dict(): Converts the parameters instance into a dictionary with key-value pairs, suitable for serialization or passing to other components.
        Converts date strings to UNIX timestamps where applicable.
    """

    backtest_name: str
    strategy_name: str
    capital: int
    schema: Schema
    data_type: LiveDataType
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    risk_free_rate: float = 0.4
    symbols: List[Symbol] = field(default_factory=list)

    # Derived attribute, not directly passed by the user
    tickers: List[str] = field(default_factory=list)

    def __post_init__(self):
        # Type checks
        if not isinstance(self.strategy_name, str):
            raise TypeError("'strategy_name' field must be of type str.")
        if not isinstance(self.capital, int):
            raise TypeError("'capital' field must be of type int.")
        if not isinstance(self.data_type, LiveDataType):
            raise TypeError(
                "'data_type' field must be an instance of MarketDataType."
            )
        if not isinstance(self.train_start, str):
            raise TypeError("'train_start' field must be of type str.")
        if not isinstance(self.train_end, str):
            raise TypeError("'train_end' field must be of type str.")
        if not isinstance(self.test_start, str):
            raise TypeError("'test_start' field must be of type str.")
        if not isinstance(self.test_end, str):
            raise TypeError("'test_end' field must be of type str.")
        if not isinstance(self.risk_free_rate, (int, float)):
            raise TypeError(
                "'risk_free_rate' field must be of type int or float."
            )
        if not isinstance(self.symbols, list):
            raise TypeError("'symbols' field must be of type list.")
        if not all(isinstance(symbol, Symbol) for symbol in self.symbols):
            raise TypeError(
                "All items in 'symbols' field must be instances of Symbol"
            )

        # Constraint checks
        if self.capital <= 0:
            raise ValueError("'capital' field must be greater than zero.")

        # # Populate the tickers list based on the provided symbols
        self.tickers = [symbol.midas_ticker for symbol in self.symbols]

    def to_dict(self):
        return {
            "strategy_name": self.strategy_name,
            "capital": self.capital,
            "data_type": self.data_type.value,
            "schema": self.schema,
            "train_start": (int(iso_to_unix(self.train_start))),
            "train_end": (int(iso_to_unix(self.train_end))),
            "test_start": int(iso_to_unix(self.test_start)),
            "test_end": int(iso_to_unix(self.test_end)),
            "tickers": self.tickers,
            # "risk_free_rate": / self.risk_free_rate,
        }

    def to_mbn(self):
        return MbnParameters(
            strategy_name=self.strategy_name,
            capital=self.capital,
            data_type=self.data_type.value,
            schema=self.schema,
            train_start=(int(iso_to_unix(self.train_start))),
            train_end=(int(iso_to_unix(self.train_end))),
            test_start=int(iso_to_unix(self.test_start)),
            test_end=int(iso_to_unix(self.test_end)),
            tickers=self.tickers,
        )

    # def to_mbn_parameters(self):
    #     return Parameters(
    #         strategy_name=self.strategy_name,
    #         capital=self.capital,
    #         schema=self.schema,
    #         data_type=self.data_type,
    #         train_start=self.train_start,
    #         train_end=self.train_end,
    #         test_start: int,
    #         test_end: int,
    #
    #
    #     )

    @classmethod
    def from_dict(cls, data: dict) -> "Parameters":
        # Validate data_type
        data_type = LiveDataType[data["data_type"].upper()]

        # Parse and map symbols
        symbols = []
        for symbol_data in data["symbols"]:
            symbols.append(SymbolFactory.from_dict(symbol_data))

        # Create and return Parameters instance
        return cls(
            backtest_name=data["backtest_name"],
            strategy_name=data["strategy_name"],
            capital=data["capital"],
            data_type=data_type,
            train_start=data["train_start"],
            train_end=data["train_end"],
            test_start=data["test_start"] or data["train_end"],
            symbols=symbols,
            schema=data["schema"],
            test_end=data["test_end"] or datetime.now().strftime("%Y-%m-%d"),
            risk_free_rate=data["risk_free_rate"],
        )

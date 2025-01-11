import toml
from enum import Enum
from typing import List
from dataclasses import dataclass, field
from mbn import Schema, Parameters as MbnParameters

from midastrader.utils import iso_to_unix
from midastrader.structs import Symbol, SymbolFactory


class Mode(Enum):
    LIVE = "LIVE"
    BACKTEST = "BACKTEST"


class LiveDataType(Enum):
    TICK = "TICK"
    BAR = "BAR"


class Config:
    """
    Unified Config class to manage configuration data for the trading system.

    This class loads configuration settings for general, database, strategy, risk, broker, and data sources
    from a TOML configuration file.

    Attributes:
        general (dict): General configuration settings like session ID, log level, and file paths.
        database (dict): Database connection details, including URL and authentication keys.
        strategy (dict): Strategy logic and parameters, including symbols and module/class definitions.
        risk (dict): Risk management settings, such as risk module and class.
        broker (dict): Broker-specific configurations.
        data_source (dict): Settings for data sources like historical or live data feeds.
        session_id (str): Unique session identifier for the trading system.
        log_level (str): Logging level, defaulting to "INFO".
        log_output (str): Output method for logs (e.g., "file" or "console").
        output_path (str): Path for saving output files.
        train_data_file (str): Path to the training dataset file.
        test_data_file (str): Path to the testing dataset file.
        data_file (str): Path to general data files.
        database_url (str): URL for connecting to the database.
        database_key (str): Authentication key for the database.
        strategy_module (str): Path to the strategy logic module.
        strategy_class (str): Class name of the trading strategy.
        strategy_parameters (dict): Parameters for configuring the trading strategy.
        risk_module (str): Path to the risk management module.
        risk_class (str): Class name of the risk management logic.
    """

    def __init__(self, config_dict: dict):
        """
        Initialize the Config class with configuration data loaded from a dictionary.

        Args:
            config_dict (dict): Dictionary representation of the loaded TOML configuration file.
        """
        self.vendors = config_dict.get("vendor")
        self.executors = config_dict.get("executor")
        self.general = config_dict.get("general", {})
        self.risk = config_dict.get("risk", {})
        self.strategy = config_dict.get("strategy", {})

        # General settings
        self.session_id = self.general.get("session_id")
        self.log_level = self.general.get("log_level", "INFO")
        self.log_output = self.general.get("log_output", "file")
        self.output_path = self.general.get("output_path", "")

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
        Load the configuration from a TOML file and initialize the Config object.

        Args:
            config_path (str): File path to the TOML configuration file.

        Returns:
            Config: An instance of the Config class populated with the TOML data.
        """
        with open(config_path, "r") as f:
            config_dict = toml.load(f)
        return cls(config_dict)


@dataclass
class Parameters:
    """
    Holds all configuration parameters necessary for setting up and running a trading strategy.

    This class manages settings like capital allocation, market data types, and time periods for testing and training.
    It also ensures validation of provided values for logical consistency.

    Attributes:
        strategy_name (str): The name of the trading strategy.
        capital (int): The amount of capital allocated for the strategy (applies to backtesting).
        schema (Schema): Schema object for data validation or structure.
        data_type (LiveDataType): The type of market data used (e.g., TICK, BAR).
        start (str): Start date of the strategy in 'YYYY-MM-DD' format.
        end (str): End date of the strategy in 'YYYY-MM-DD' format.
        risk_free_rate (float): The risk-free rate used for performance calculations. Default is 0.4.
        symbols (List[Symbol]): List of trading symbols involved in the strategy.
        tickers (List[str]): Derived list of ticker symbols extracted from the `symbols` attribute.

    Methods:
        to_dict():
            Converts the Parameters instance into a dictionary, serializing date strings into UNIX timestamps.

        to_mbn():
            Converts the Parameters instance into `MbnParameters` format for integration with the `mbn` module.

        from_dict(data: dict) -> Parameters:
            Constructs a Parameters instance from a dictionary, validating and mapping its fields.
    """

    strategy_name: str
    capital: int
    schema: Schema
    data_type: LiveDataType
    start: str
    end: str
    risk_free_rate: float = 0.4
    symbols: List[Symbol] = field(default_factory=list)

    # Derived attribute, not directly passed by the user
    tickers: List[str] = field(default_factory=list)

    def __post_init__(self):
        """
        Post-initialization method to validate input fields and generate derived attributes.

        Raises:
            TypeError: If fields have invalid types.
            ValueError: If constraints like capital <= 0 are violated.
        """
        # Type checks
        if not isinstance(self.strategy_name, str):
            raise TypeError("'strategy_name' must be of type str.")
        if not isinstance(self.capital, int):
            raise TypeError("'capital' must be of type int.")
        if not isinstance(self.data_type, LiveDataType):
            raise TypeError("'data_type' must be of type LiveDataType.")
        if not isinstance(self.start, str):
            raise TypeError("'start' must be of type str.")
        if not isinstance(self.end, str):
            raise TypeError("'end' must be of type str.")
        if not isinstance(self.risk_free_rate, (int, float)):
            raise TypeError("'risk_free_rate' must be of type int or float.")
        if not isinstance(self.symbols, list):
            raise TypeError("'symbols' must be of type list.")
        if not all(isinstance(symbol, Symbol) for symbol in self.symbols):
            raise TypeError("All 'symbols' must be instances of Symbol")

        # Constraint checks
        if self.capital <= 0:
            raise ValueError("'capital' must be greater than zero.")

        # # Populate the tickers list based on the provided symbols
        self.tickers = [symbol.midas_ticker for symbol in self.symbols]

    def to_dict(self) -> dict:
        """
        Converts the Parameters instance into a dictionary representation.

        Date strings (`start`, `end`) are converted into UNIX timestamps.

        Returns:
            dict: A dictionary with serialized key-value pairs.
        """
        return {
            "strategy_name": self.strategy_name,
            "capital": self.capital,
            "data_type": self.data_type.value,
            "schema": self.schema,
            "start": (int(iso_to_unix(self.start))),
            "end": (int(iso_to_unix(self.end))),
            "tickers": self.tickers,
        }

    def to_mbn(self) -> MbnParameters:
        """
        Converts the Parameters instance into an `MbnParameters` object.

        Returns:
            MbnParameters: Object formatted for compatibility with the `mbn` module.
        """
        return MbnParameters(
            strategy_name=self.strategy_name,
            capital=self.capital,
            data_type=self.data_type.value,
            schema=self.schema,
            start=(int(iso_to_unix(self.start))),
            end=(int(iso_to_unix(self.end))),
            tickers=self.tickers,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Parameters":
        """
        Constructs a Parameters instance from a dictionary.

        Args:
            data (dict): Dictionary containing configuration fields.

        Returns:
            Parameters: A populated Parameters instance.

        Raises:
            KeyError: If required fields are missing.
            ValueError: If data fields fail validation.
        """
        # Validate data_type
        data_type = LiveDataType[data["data_type"].upper()]

        # Parse and map symbols
        symbols = []
        for symbol_data in data["symbols"]:
            symbols.append(SymbolFactory.from_dict(symbol_data))

        # Create and return Parameters instance
        return cls(
            strategy_name=data["strategy_name"],
            capital=data["capital"],
            data_type=data_type,
            start=data["start"],
            end=data["end"],
            symbols=symbols,
            schema=data["schema"],
            risk_free_rate=data["risk_free_rate"],
        )

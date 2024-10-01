from enum import Enum
from typing import Optional, Dict, List
from ibapi.contract import Contract
from abc import ABC, abstractmethod
from midas.orders import Action
from dataclasses import dataclass, field
from datetime import time, datetime
import pandas as pd
import pandas_market_calendars as mcal
from midas.utils.unix import unix_to_date
from datetime import timedelta
from midas.utils.unix import unix_to_iso


# -- Symbol Details --
class AssetClass(Enum):
    EQUITY = "EQUITY"
    COMMODITY = "COMMODITY"
    FIXED_INCOME = "FIXED_INCOME"
    FOREX = "FOREX"
    CRYPTOCURRENCY = "CRYPTOCURRENCY"


class SecurityType(Enum):
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    CRYPTO = "CRYPTO"
    INDEX = "IND"
    BOND = "BOND"
    # ['STK', 'CMDTY','FUT','OPT','CASH','CRYPTO','FIGI','IND','CFD','FOP','BOND']


class Venue(Enum):
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    CME = "CME"
    CBOT = "CBOT"
    CBOE = "CBOE"
    COMEX = "COMEX"
    GLOBEX = "GLOBEX"
    NYMEX = "NYMEX"
    INDEX = "INDEX"  # Specific for the creation of indexes
    SMART = "SMART"  # IB specific
    ISLAND = "ISLAND"  # IB specific


class Currency(Enum):
    USD = "USD"
    CAD = "CAD"
    EUR = "EUR"
    GBP = "GBP"
    AUD = "AUD"
    JPY = "JPY"


class Industry(Enum):
    # Equities
    ENERGY = "Energy"
    MATERIALS = "Materials"
    INDUSTRIALS = "Industrials"
    UTILITIES = "Utilities"
    HEALTHCARE = "Healthcare"
    FINANCIALS = "Financials"
    CONSUMER = "Consumer"
    TECHNOLOGY = "Technology"
    COMMUNICATION = "Communication"
    REAL_ESTATE = "Real Estate"

    # Commodities
    METALS = "Metals"
    AGRICULTURE = "Agriculture"


class ContractUnits(Enum):
    BARRELS = "Barrels"
    BUSHELS = "Bushels"
    POUNDS = "Pounds"
    TROY_OUNCE = "Troy Ounce"
    METRIC_TON = "Metric Ton"
    SHORT_TON = "Short Ton"


class Right(Enum):
    CALL = "CALL"
    PUT = "PUT"


class FuturesMonth(Enum):
    F = 1  # JANUARY
    G = 2  # FEB
    H = 3  # MAR
    J = 4  # APR
    K = 5  # MAY
    M = 6  # JUN
    N = 7  # JULY
    Q = 8  # AUG
    U = 9  # SEPT
    V = 10  # OCT
    X = 11  # NOV
    Z = 12  # DEC


@dataclass
class TradingSession:
    day_open: time
    day_close: time
    night_open: Optional[time] = None
    night_close: Optional[time] = None
    # Optional third session for Asian markets (commented out for now)
    # third_session_open: Optional[time] = None
    # third_session_close: Optional[time] = None

    def __post_init__(self):
        """
        Ensure that time windows are correctly defined for day and night sessions.
        """
        if self.day_open and not self.day_close:
            raise ValueError(
                "Day session must have both open and close times."
            )
        if self.night_open and not self.night_close:
            raise ValueError(
                "Night session must have both open and close times."
            )
        if not (self.day_open or self.night_open):
            raise ValueError("One session (day or night) must be defined.")


# -- Symbols --
@dataclass
class Symbol(ABC):
    instrument_id: int
    broker_ticker: str
    data_ticker: str
    midas_ticker: str
    security_type: SecurityType
    currency: Currency
    exchange: Venue
    fees: float
    initial_margin: float
    quantity_multiplier: int
    price_multiplier: float
    trading_sessions: TradingSession
    slippage_factor: float
    contract: Contract = field(init=False)

    def __post_init__(self):
        # Type Validation
        if not isinstance(self.instrument_id, int):
            raise TypeError("'instrument_id' field must be of type int.")
        if not isinstance(self.broker_ticker, str):
            raise TypeError("'broker_ticker' field must be of type str.")
        if not isinstance(self.security_type, SecurityType):
            raise TypeError(
                "'security_type' field must be of type SecurityType."
            )
        if not isinstance(self.currency, Currency):
            raise TypeError("'currency' field must be enum instance Currency.")
        if not isinstance(self.exchange, Venue):
            raise TypeError("'exchange' field must be enum instance Venue.")
        if not isinstance(self.fees, (float, int)):
            raise TypeError("'fees' field must be int or float.")
        if not isinstance(self.initial_margin, (float, int)):
            raise TypeError("'initial_margin' field must be an int or float.")
        if not isinstance(self.quantity_multiplier, (float, int)):
            raise TypeError(
                "'quantity_multiplier' field must be of type int or float."
            )
        if not isinstance(self.price_multiplier, (float, int)):
            raise TypeError(
                "'price_multiplier' field must be of type int or float."
            )
        if not isinstance(self.slippage_factor, (float, int)):
            raise TypeError(
                "'slippage_factor' field must be of type int or float."
            )
        if not isinstance(self.data_ticker, str):
            raise TypeError("'data_ticker' field must be a string or None.")

        # Constraint Validation
        if self.fees < 0:
            raise ValueError("'fees' field cannot be negative.")
        if self.initial_margin < 0:
            raise ValueError("'initial_margin' field must be non-negative.")
        if self.price_multiplier <= 0:
            raise ValueError(
                "'price_multiplier' field must be greater than zero."
            )
        if self.quantity_multiplier <= 0:
            raise ValueError(
                "'quantity_multiplier' field must be greater than zero."
            )
        if self.slippage_factor < 0:
            raise ValueError(
                "'slippage_factor' field must be greater than zero."
            )

    def to_contract_data(self) -> dict:
        """
        Constructs a dictionary from instance variables used in the construction of Contract object.

        Returns:
        - dict : Representing the data to be added to Contract object.
        """
        return {
            "symbol": self.broker_ticker,
            "secType": self.security_type.value,
            "currency": self.currency.value,
            "exchange": self.exchange.value,
            "multiplier": self.quantity_multiplier,
        }

    def to_contract(self) -> Contract:
        """
        Creates a ibapi Contract object from instance data.

        Returns:
        - Contract: Object unique to the symbol used in the ibapi library.
        """
        try:
            contract_data = self.to_contract_data()
            contract = Contract()
            for key, value in contract_data.items():
                setattr(contract, key, value)
            return contract
        except Exception as e:
            raise Exception(f"Unexpected error during Contract creation: {e}")

    def to_dict(self):
        return {
            "ticker": self.midas_ticker,
            "security_type": self.security_type.value,
        }

    def commission_fees(self, quantity: float) -> float:
        """
        Calculates the commission fees for an order based on the quantity.

        Parameters:
        - quantity (float): The quantity of the order.

        Returns:
        - float: The calculated commission fees.
        """
        return abs(quantity) * self.fees * -1

    def slippage_price(self, current_price: float, action: Action) -> float:
        """
        Adjusts the current price based on slippage factor.

        Parameters:
        - current_price (float): The current market price of the symbol.
        - action (Action): The action associated with the order (LONG, SHORT, etc.). Used to determine which way to adjust price.

        Returns:
        - float: The adjusted price after accounting for slippage.
        """
        if action in [Action.LONG, Action.COVER]:  # Buying
            adjusted_price = current_price + self.slippage_factor
        elif action in [Action.SHORT, Action.SELL]:  # Selling
            adjusted_price = current_price - self.slippage_factor
        else:
            raise ValueError("'action' must be of type Action enum.")

        return adjusted_price

    def after_day_session(self, timestamp_ns: int) -> bool:
        dt = datetime.fromisoformat(
            unix_to_iso(timestamp_ns, tz_info="America/New_York")
        )
        time = dt.time()

        if self.trading_sessions.day_close < time:
            return True
        return False

    def in_day_session(self, timestamp_ns: int) -> bool:
        dt = datetime.fromisoformat(
            unix_to_iso(timestamp_ns, tz_info="America/New_York")
        )
        time = dt.time()

        # Check if the time falls within any of the trading sessions
        if (
            self.trading_sessions.day_open
            <= time
            <= self.trading_sessions.day_close
        ):
            return True
        return False

    @abstractmethod
    def value(self, quantity: float, price: Optional[float] = None) -> float:
        pass

    @abstractmethod
    def cost(self, quantity: float, price: Optional[float] = None) -> float:
        pass


@dataclass
class Equity(Symbol):
    company_name: str
    industry: Industry
    market_cap: float
    shares_outstanding: int

    def __post_init__(self):
        self.security_type = SecurityType.STOCK
        super().__post_init__()
        # Type checks
        if not isinstance(self.company_name, str):
            raise TypeError("'company_name' field must be of type str.")
        if not isinstance(self.industry, Industry):
            raise TypeError("'industry' field must be of type Industry.")
        if not isinstance(self.market_cap, float):
            raise TypeError("'market_cap' field must be of type float.")
        if not isinstance(self.shares_outstanding, int):
            raise TypeError("'shares_outstanding' feild must be of type int.")

        # Create contract object
        self.contract = self.to_contract()

    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        return data

    def to_dict(self):
        symbol_dict = super().to_dict()
        symbol_dict["symbol_data"] = {
            "company_name": self.company_name,
            "venue": self.exchange.value,
            "currency": self.currency.value,
            "industry": self.industry.value,
            "market_cap": self.market_cap,
            "shares_outstanding": self.shares_outstanding,
        }
        return symbol_dict

    def value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the value of an equity,

        Parameters:
        - quantity (float): The quantity of the equity.
        - price (float): The price of the equity.

        Returns:
        - float: The calculated value of the equity.
        """
        return quantity * price

    def cost(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the cost of owning an equity,

        Parameters:
        - quantity (float): The quantity of the equity.
        - price (float): The price of the equity.

        Returns:
        - float: The calculated cost of owning the equity.
        """
        return abs(quantity) * price


@dataclass
class Future(Symbol):
    product_code: str
    product_name: str
    industry: Industry
    contract_size: float
    contract_units: ContractUnits
    tick_size: float
    min_price_fluctuation: float
    continuous: bool
    lastTradeDateOrContractMonth: str
    expr_months: List[FuturesMonth]
    term_day_rule: str
    market_calendar: str

    def __post_init__(self):
        self.security_type = SecurityType.FUTURE
        super().__post_init__()
        # Type checks
        if not isinstance(self.product_code, str):
            raise TypeError("'product_code' field must be of type str.")
        if not isinstance(self.product_name, str):
            raise TypeError("'product_name' field must be of type str.")
        if not isinstance(self.industry, Industry):
            raise TypeError("'industry' field must be of type Industry.")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError(
                "'contract_size' field must be of type int or float."
            )
        if not isinstance(self.contract_units, ContractUnits):
            raise TypeError(
                "'contract_units' field must be of type ContractUnits."
            )
        if not isinstance(self.tick_size, (int, float)):
            raise TypeError("'tick_size' field must be of type int or float.")
        if not isinstance(self.min_price_fluctuation, (int, float)):
            raise TypeError(
                "'min_price_fluctuation' field must be of type int or float."
            )
        if not isinstance(self.continuous, bool):
            raise TypeError("'continuous' field must be of type boolean.")
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError(
                "'lastTradeDateOrContractMonth' field must be a string."
            )
        for month in self.expr_months:
            if not isinstance(month, FuturesMonth):
                raise TypeError(
                    "'expr_month' must a list of type FuturesMonth."
                )
        if not isinstance(self.term_day_rule, str):
            raise TypeError("'term_day_rule' field must be of type str.")

        # Constraint Checks
        if self.tick_size <= 0:
            raise ValueError("'tickSize' field must be greater than zero.")

        # Create contract object
        self.contract = self.to_contract()

    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = (
            self.lastTradeDateOrContractMonth
        )
        return data

    def to_dict(self):
        symbol_dict = super().to_dict()
        symbol_dict["symbol_data"] = {
            "product_code": self.product_code,
            "product_name": self.product_name,
            "venue": self.exchange.value,
            "currency": self.currency.value,
            "industry": self.industry.value,
            "contract_size": self.contract_size,
            "contract_units": self.contract_units.value,
            "tick_size": self.tick_size,
            "min_price_fluctuation": self.min_price_fluctuation,
            "continuous": self.continuous,
        }
        return symbol_dict

    def value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the value of a futures contract.

        Parameters:
        - quantity (float): The numnber of contracts of the given future.
        - price (float): The price of a single contract.

        Returns:
        - float: The calculated value for the given quantity of futures at the given price.
        """
        return (
            self.price_multiplier * price * quantity * self.quantity_multiplier
        )

    def cost(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the cost to own a quantity of the instance contract.

        Parameters:
        - quantity (float): The quantity of the future order.

        Returns:
        - float: The calculated margin requirement for the future order.
        """
        return abs(quantity) * self.initial_margin

    def in_rolling_window(
        self,
        ts: int,
        window: int = 2,
        tz_info="UTC",
    ) -> bool:
        """
        Check if the timestamp falls within the rolling window before the termination date.

        Parameters:
        - ts (int): The timestamp in nanoseconds.
        - window (int): The rolling window size in days (defaults to 2).
        - tz_info (str): The timezone information (defaults to "UTC").

        Returns:
        - bool: Whether the timestamp is within the rolling window of the termination period.
        """
        # Convert the timestamp into a datetime object
        event_date = unix_to_date(ts, tz_info)

        # Extract the year and month from the event_date
        year = event_date.year
        month = event_date.month

        if month in [month.value for month in self.expr_months]:
            # Get the termination date for the current contract month/year
            termination_date = self.apply_day_rule(month, year).date()

            # Calculate the rolling window period
            window_start = termination_date - timedelta(days=window)
            window_end = termination_date + timedelta(days=window)

            # Check if the event date falls within the rolling window
            return window_start <= event_date <= window_end
        else:
            return False

    def apply_day_rule(self, month: int, year: int) -> datetime:
        """
        Apply the user-friendly day rule to determine the expiration date.
        """
        # Match "nth_business_day_10"
        if self.term_day_rule.startswith("nth_business_day"):
            nth_day = int(self.term_day_rule.split("_")[-1])
            return self.get_nth_business_day(
                month,
                year,
                nth_day,
                self.market_calendar,
            )
        # Match "nth_last_business_day_2"
        elif self.term_day_rule.startswith("nth_last_business_day"):
            nth_last_day = int(self.term_day_rule.split("_")[-1])
            return self.get_nth_last_business_day(
                month,
                year,
                nth_last_day,
                self.market_calendar,
            )
        # Match "nth_business_day_before_nth_day_2_15"
        elif self.term_day_rule.startswith("nth_bday_before_nth_day"):
            parts = self.term_day_rule.split("_")
            nth_day = int(parts[-1])
            target_day = int(parts[-2])
            return self.get_nth_business_day_before(
                month,
                year,
                target_day,
                nth_day,
                self.market_calendar,
            )
        else:
            raise ValueError(f"Unknown rule: {self.term_day_rule}")

    @staticmethod
    def get_nth_business_day(
        month: int,
        year: int,
        nth_day: int,
        market_calendar: str,
    ) -> datetime:
        """
        Get the nth business day of the specified month and year.
        """
        start_date = pd.Timestamp(year, month, 1)
        year = year if month < 12 else year + 1
        month = month if month < 12 else 0

        end_date = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)

        # Get the valid trading days for the given month
        calendar = mcal.get_calendar(market_calendar)
        trading_days = calendar.valid_days(
            start_date=start_date,
            end_date=end_date,
        )
        return trading_days[nth_day - 1]  # Return the nth trading day

    @staticmethod
    def get_nth_last_business_day(
        month: int,
        year: int,
        nth_last_day: int,
        market_calendar: str,
    ) -> datetime:
        """
        Get the nth last business day of the specified month and year.
        """
        start_date = pd.Timestamp(year, month, 1)
        year = year if month < 12 else year + 1
        month = month if month < 12 else 0

        end_date = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)

        calendar = mcal.get_calendar(market_calendar)
        trading_days = calendar.valid_days(
            start_date=start_date,
            end_date=end_date,
        )

        return trading_days[-nth_last_day]

    @staticmethod
    def get_nth_business_day_before(
        month: FuturesMonth,
        year: int,
        target_day: int,
        nth_day: int,
        market_calendar: str,
    ) -> datetime:
        """
        Get the nth business day before the specified target day in the given month and year.
        """
        start_date = pd.Timestamp(year, month, 1)
        end_date = pd.Timestamp(year, month, nth_day)

        calendar = mcal.get_calendar(market_calendar)
        trading_days = calendar.valid_days(
            start_date=start_date,
            end_date=end_date,
        )
        return trading_days[-target_day]


@dataclass
class Option(Symbol):
    strike_price: float
    expiration_date: str
    option_type: Right
    contract_size: int
    underlying_name: str
    lastTradeDateOrContractMonth: str

    def __post_init__(self):
        self.security_type = SecurityType.OPTION
        super().__post_init__()
        # Type checks
        if not isinstance(self.strike_price, (int, float)):
            raise TypeError(
                "'strike_price' field must be of type int or float."
            )
        if not isinstance(self.expiration_date, str):
            raise TypeError("'expiration_date' field must be of type str.")
        if not isinstance(self.option_type, Right):
            raise TypeError("'option_type' field must be of type Right.")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError(
                "'contract_size' field must be of type int or float."
            )
        if not isinstance(self.underlying_name, str):
            raise TypeError("'underlying_name' must be of type str.")
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError(
                "'lastTradeDateOrContractMonth' field must be a string."
            )

        # Constraint checks
        if self.strike_price <= 0:
            raise ValueError("'strike' field must be greater than zero.")

        # Create contract object
        self.contract = self.to_contract()

    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = (
            self.lastTradeDateOrContractMonth
        )
        data["right"] = self.option_type.value
        data["strike"] = self.strike_price
        return data

    def to_dict(self):
        symbol_dict = super().to_dict()
        symbol_dict["symbol_data"] = {
            "strike_price": self.strike_price,
            "currency": self.currency.value,
            "venue": self.exchange.value,
            "expiration_date": self.expiration_date,
            "option_type": self.option_type.value,
            "contract_size": self.contract_size,
            "underlying_name": self.underlying_name,
        }
        return symbol_dict

    def value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the market value of the option position based on the premium price.

        Parameters:
        - quantity (float): The number of contracts.
        - price (Optional[float]): The premium price of the option.

        Returns:
        - float: The market value of the option position.
        """
        if price is None:
            raise ValueError("Price must be provided to calculate value.")
        return abs(quantity) * price * self.quantity_multiplier

    def cost(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the cost to acquire the option position based on the premium price.

        Parameters:
        - quantity (float): The number of contracts.
        - price (Optional[float]): The premium price of the option.

        Returns:
        - float: The cost to acquire the option position.
        """
        if price is None:
            raise ValueError("Price must be provided to calculate cost.")

        return abs(quantity) * price * self.quantity_multiplier


# @dataclass
# class Index(Symbol):
#     name: str
#     asset_class: AssetClass
#
#     def __post_init__(self):
#         # Default
#         fees: float = 0.0
#         initial_margin: float = 0.0
#         quantity_multiplier: int = 1
#         price_multiplier: float = 1.0
#         exchange: Venue = Venue.INDEX
#         security_type: SecurityType = SecurityType.INDEX
#         super().__post_init__()
#         # Type checks
#         if not isinstance(self.name, str):
#             raise TypeError("'name' field must be of type str.")
#         if not isinstance(self.asset_class, AssetClass):
#             raise TypeError("'asset_class' field must be of type AssetClass.")
#
#     def to_dict(self):
#         symbol_dict = super().to_dict()
#         symbol_dict["symbol_data"] = {
#             "name": self.name,
#             "currency": self.currency.value,
#             "asset_class": self.asset_class.value,
#             "venue": self.exchange.value,
#         }
#         return symbol_dict
#
#     def value(self, quantity: float, price: Optional[float] = None) -> float:
#         pass
#
#     def cost(self, quantity: float, price: Optional[float] = None) -> float:
#         pass
#


class SymbolFactory:
    @classmethod
    def _get_symbol_class(cls, symbol_type: str):
        """
        Returns the appropriate Symbol subclass based on the provided symbol type.
        """
        if symbol_type == "Equity":
            return Equity
        elif symbol_type == "Future":
            return Future
        elif symbol_type == "Option":
            return Option
        # elif symbol_type == "Index":
        #     return Index
        else:
            raise ValueError(f"Unknown symbol type: {symbol_type}")

    @classmethod
    def _parse_time(cls, time_str: str) -> time:
        """
        Parse time from string in 'HH:MM' format.
        """
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)

    @classmethod
    def _map_symbol_enum_fields(cls, symbol_data: dict) -> dict:
        """
        Maps string values to the appropriate enum types.
        """
        symbol_data["currency"] = Currency[symbol_data["currency"].upper()]
        symbol_data["security_type"] = SecurityType[
            symbol_data["security_type"].upper()
        ]
        symbol_data["exchange"] = Venue[symbol_data["exchange"].upper()]

        if "industry" in symbol_data:
            symbol_data["industry"] = Industry[symbol_data["industry"].upper()]

        if "contract_units" in symbol_data:
            symbol_data["contract_units"] = ContractUnits[
                symbol_data["contract_units"].upper()
            ]

        if "option_type" in symbol_data:
            symbol_data["option_type"] = Right[symbol_data["option_type"]]

        if "expr_months" in symbol_data:
            symbol_data["expr_months"] = [
                FuturesMonth[month] for month in symbol_data["expr_months"]
            ]

        return symbol_data

    @classmethod
    def from_dict(cls, symbol_data: dict) -> Symbol:
        """
        Parse a single symbol from a dictionary format, creating a symbol object.
        """
        symbol_type = symbol_data.pop("type")
        symbol_class = cls._get_symbol_class(symbol_type)

        # Parse trading sessions
        sessions_data = symbol_data.pop("trading_sessions", {})
        trading_session = TradingSession(
            day_open=cls._parse_time(sessions_data.get("day_open")),
            day_close=cls._parse_time(sessions_data.get("day_close")),
            night_open=(
                cls._parse_time(sessions_data.get("night_open"))
                if sessions_data.get("night_open")
                else None
            ),
            night_close=(
                cls._parse_time(sessions_data.get("night_open"))
                if sessions_data.get("night_close")
                else None
            ),
        )

        symbol_data["trading_sessions"] = trading_session

        # Map enum fields
        symbol_data = cls._map_symbol_enum_fields(symbol_data)

        return symbol_class(**symbol_data)


class SymbolMap:
    def __init__(self):
        """
        Initializes the SymbolMap with a universal mapping of symbols by instrument ID
        and their corresponding tickers from different providers.
        """
        # Maps the instrument ID to the Symbol object
        self.map: Dict[int, Symbol] = {}

        # Maps broker/data/midas tickers to instrument IDs
        self.broker_map: Dict[str, int] = {}
        self.data_map: Dict[str, int] = {}
        self.midas_map: Dict[str, int] = {}

    def add_symbol(
        self,
        symbol: Symbol,
    ) -> None:
        """
        Add the symbol to the map, linking the universal instrument ID to the symbol
        and its associated tickers (broker, data, midas).

        Parameters:
        - instrument_id (int): The universal instrument ID.
        - broker_ticker (str): The ticker used by the broker.
        - data_ticker (str): The ticker used by the data provider.
        - midas_ticker (str): The ticker used by the internal system (midas).
        - symbol (Symbol): The Symbol object to add to the map.
        """
        # Map the tickers to the instrument ID
        self.broker_map[symbol.broker_ticker] = symbol.instrument_id
        self.data_map[symbol.data_ticker] = symbol.instrument_id
        self.midas_map[symbol.midas_ticker] = symbol.instrument_id

        # Associate the instrument ID with the symbol
        self.map[symbol.instrument_id] = symbol

    def get_symbol(self, ticker: str) -> Symbol:
        """
        Retrieve the symbol by any ticker (broker, data, or midas).

        Parameters:
        - ticker (str): The broker, data, or midas ticker.

        Returns:
        - Symbol: The symbol associated with the provided ticker, or None if not found.
        """
        instrument_id = self.get_id(ticker)
        return self.map.get(instrument_id)

    def get_id(self, ticker: str) -> int:
        instrument_id = (
            self.broker_map.get(ticker)
            or self.data_map.get(ticker)
            or self.midas_map.get(ticker)
        )
        return instrument_id

    @property
    def symbols(self) -> List[Symbol]:
        # Return the list of all unique symbols
        return list(self.map.values())

    @property
    def instrument_ids(self) -> List[int]:
        return list(self.map.keys())

    @property
    def broker_tickers(self) -> List[str]:
        # Return just the broker tickers
        return list(self.broker_map.keys())

    @property
    def data_tickers(self) -> List[str]:
        # Return just the data tickers
        return list(self.data_map.keys())

    @property
    def midas_tickers(self) -> List[str]:
        # Return just the midas tickers
        return list(self.midas_map.keys())

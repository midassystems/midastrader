# noqa: C901
import pandas as pd
import pandas_market_calendars as mcal
from enum import Enum
from typing import Optional, Dict, List
from ibapi.contract import Contract
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import time, datetime
from datetime import timedelta

from midastrader.structs.orders import Action
from midastrader.utils.unix import unix_to_date, unix_to_iso


# -- Symbol Details --
class AssetClass(Enum):
    """
    Represents the broad classification of financial assets.

    Values:
        EQUITY: Equity or stock assets.
        COMMODITY: Commodities like metals, oil, etc.
        FIXED_INCOME: Fixed income instruments like bonds.
        FOREX: Foreign exchange currencies.
        CRYPTOCURRENCY: Digital or cryptocurrency assets.
    """

    EQUITY = "EQUITY"
    COMMODITY = "COMMODITY"
    FIXED_INCOME = "FIXED_INCOME"
    FOREX = "FOREX"
    CRYPTOCURRENCY = "CRYPTOCURRENCY"


class SecurityType(Enum):
    """
    Represents the specific type of a financial security.

    Values:
        STOCK: Stocks or equities.
        OPTION: Options contracts.
        FUTURE: Futures contracts.
        CRYPTO: Cryptocurrency instruments.
        INDEX: Index instruments.
        BOND: Fixed income or bond instruments.
    """

    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    CRYPTO = "CRYPTO"
    INDEX = "IND"
    BOND = "BOND"


class Venue(Enum):
    """
    Represents the trading venue or exchange where financial instruments are traded.

    Values:
        NASDAQ: NASDAQ Exchange.
        NYSE: New York Stock Exchange.
        CME: Chicago Mercantile Exchange.
        CBOT: Chicago Board of Trade.
        CBOE: Chicago Board Options Exchange.
        COMEX: Commodity Exchange.
        GLOBEX: Electronic futures trading platform.
        NYMEX: New York Mercantile Exchange.
        INDEX: For index-related operations.
        SMART: Interactive Brokers smart routing.
        ISLAND: Interactive Brokers-specific venue.
    """

    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    CME = "CME"
    CBOT = "CBOT"
    CBOE = "CBOE"
    COMEX = "COMEX"
    GLOBEX = "GLOBEX"
    NYMEX = "NYMEX"
    INDEX = "INDEX"
    SMART = "SMART"
    ISLAND = "ISLAND"


class Currency(Enum):
    """
    Represents commonly traded global currencies.

    Values:
        USD: US Dollar.
        CAD: Canadian Dollar.
        EUR: Euro.
        GBP: British Pound.
        AUD: Australian Dollar.
        JPY: Japanese Yen.
    """

    USD = "USD"
    CAD = "CAD"
    EUR = "EUR"
    GBP = "GBP"
    AUD = "AUD"
    JPY = "JPY"


class Industry(Enum):
    """
    Represents the industry classification for equities and commodities.

    Values:
        ENERGY: Energy sector.
        MATERIALS: Materials sector.
        INDUSTRIALS: Industrial sector.
        UTILITIES: Utilities sector.
        HEALTHCARE: Healthcare sector.
        FINANCIALS: Financial sector.
        CONSUMER: Consumer goods sector.
        TECHNOLOGY: Technology sector.
        COMMUNICATION: Communication services.
        REAL_ESTATE: Real estate sector.
        METALS: Metals commodities.
        AGRICULTURE: Agricultural commodities.
    """

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
    METALS = "Metals"
    AGRICULTURE = "Agriculture"


class ContractUnits(Enum):
    """
    Represents the units of measurement for commodity contracts.

    Values:
        BARRELS: Measurement in barrels (e.g., crude oil).
        BUSHELS: Measurement in bushels (e.g., grains).
        POUNDS: Measurement in pounds.
        TROY_OUNCE: Measurement in troy ounces (e.g., gold, silver).
        METRIC_TON: Measurement in metric tons.
        SHORT_TON: Measurement in short tons.
    """

    BARRELS = "Barrels"
    BUSHELS = "Bushels"
    POUNDS = "Pounds"
    TROY_OUNCE = "Troy Ounce"
    METRIC_TON = "Metric Ton"
    SHORT_TON = "Short Ton"


class Right(Enum):
    """
    Represents the type of option contract.

    Values:
        CALL: Call option.
        PUT: Put option.
    """

    CALL = "CALL"
    PUT = "PUT"


class FuturesMonth(Enum):
    """
    Maps futures contract month codes to their respective months.

    Values:
        F: January
        G: February
        H: March
        J: April
        K: May
        M: June
        N: July
        Q: August
        U: September
        V: October
        X: November
        Z: December
    """

    F = 1
    G = 2
    H = 3
    J = 4
    K = 5
    M = 6
    N = 7
    Q = 8
    U = 9
    V = 10
    X = 11
    Z = 12


class Timezones(Enum):
    """
    Represents time zones in North America.

    Values:
        PACIFIC: Pacific Time Zone.
        MOUNTAIN: Mountain Time Zone.
        CENTRAL: Central Time Zone.
        EASTERN: Eastern Time Zone.
        ATLANTIC: Atlantic Time Zone.
        NEWFOUNDLAND: Newfoundland Time Zone.
        ALASKA: Alaska Time Zone.
        HAWAII: Hawaii Time Zone.
    """

    PACIFIC = "America/Los_Angeles"
    MOUNTAIN = "America/Denver"
    CENTRAL = "America/Chicago"
    EASTERN = "America/New_York"
    ATLANTIC = "America/Halifax"
    NEWFOUNDLAND = "America/St_Johns"
    ALASKA = "America/Anchorage"
    HAWAII = "Pacific/Honolulu"

    @classmethod
    def list_timezones(cls):
        """
        Returns all available time zones as a list.

        Returns:
            list: List of timezone strings.
        """
        return [zone.value for zone in cls]

    @classmethod
    def is_valid(cls, timezone: str) -> bool:
        """
        Checks if a given string is a valid timezone.

        Args:
            timezone (str): The timezone string to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        return timezone in cls._value2member_map_


@dataclass
class TradingSession:
    """
    Represents the trading session times for an instrument.

    Attributes:
        day_open (time): Opening time for the day session.
        day_close (time): Closing time for the day session.
        night_open (Optional[time]): Opening time for the night session (optional).
        night_close (Optional[time]): Closing time for the night session (optional).
    """

    day_open: time
    day_close: time
    night_open: Optional[time] = None
    night_close: Optional[time] = None
    # Optional third session for Asian markets
    # third_session_open: Optional[time] = None
    # third_session_close: Optional[time] = None

    def __post_init__(self):
        """
        Ensures the trading session times are valid.

        Raises:
            ValueError: If open/close times are not paired correctly or if no session is defined.
        """
        if self.day_open and not self.day_close:
            raise ValueError("Day session needs open and close times.")
        if self.night_open and not self.night_close:
            raise ValueError("Night session needs open and close times.")
        if not (self.day_open or self.night_open):
            raise ValueError("One session (day or night) must be defined.")


# -- Symbols --
@dataclass
class Symbol(ABC):
    """
    Abstract base class representing a financial instrument or trading symbol.

    Attributes:
        instrument_id (int): Unique numeric identifier for the instrument.
        broker_ticker (str): Ticker symbol used by the broker.
        data_ticker (str): Ticker symbol used for data sources (e.g., market data feeds).
        midas_ticker (str): Internal ticker name for the system.
        security_type (SecurityType): Type of security (e.g., STOCK, OPTION, FUTURE).
        currency (Currency): Currency in which the instrument trades.
        exchange (Venue): Trading venue or exchange where the symbol is listed.
        fees (float): Transaction fees (e.g., commission) per unit traded.
        initial_margin (float): Margin required per unit of the instrument.
        quantity_multiplier (int): Scaling factor for quantity (e.g., lot size, contract size).
        price_multiplier (float): Scaling factor for price (e.g., futures multipliers).
        trading_sessions (TradingSession): Time window(s) for when the symbol is tradable.
        slippage_factor (float): Adjustment factor to simulate slippage in price.
        contract (Contract): Interactive Brokers API `Contract` object (created post-init).
    """

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

    def __post_init__(self):  # noqa: C901
        """
        Validates the input attributes and enforces constraints on numeric fields.

        Raises:
            TypeError: If any attribute has an invalid type.
            ValueError: If constraints like non-negative fees, margin, or multipliers are violated.
        """
        # Type Validation
        if not isinstance(self.instrument_id, int):
            raise TypeError("'instrument_id' must be of type int.")
        if not isinstance(self.broker_ticker, str):
            raise TypeError("'broker_ticker' must be of type str.")
        if not isinstance(self.security_type, SecurityType):
            raise TypeError("'security_type' must be of type SecurityType.")
        if not isinstance(self.currency, Currency):
            raise TypeError("'currency' must be enum instance Currency.")
        if not isinstance(self.exchange, Venue):
            raise TypeError("'exchange' must be enum instance Venue.")
        if not isinstance(self.fees, (float, int)):
            raise TypeError("'fees' must be int or float.")
        if not isinstance(self.initial_margin, (float, int)):
            raise TypeError("'initial_margin' must be an int or float.")
        if not isinstance(self.quantity_multiplier, (float, int)):
            raise TypeError("'quantity_multiplier' must be type int or float.")
        if not isinstance(self.price_multiplier, (float, int)):
            raise TypeError("'price_multiplier' must be of type int or float.")
        if not isinstance(self.slippage_factor, (float, int)):
            raise TypeError("'slippage_factor' must be of type int or float.")
        if not isinstance(self.data_ticker, str):
            raise TypeError("'data_ticker' must be a string or None.")

        # Constraint Validation
        if self.fees < 0:
            raise ValueError("'fees' cannot be negative.")
        if self.initial_margin < 0:
            raise ValueError("'initial_margin' must be non-negative.")
        if self.price_multiplier <= 0:
            raise ValueError("'price_multiplier' must be greater than zero.")
        if self.quantity_multiplier <= 0:
            raise ValueError("'quantity_multiplier' must be greater than 0.")
        if self.slippage_factor < 0:
            raise ValueError("'slippage_factor' must be greater than zero.")

    def to_contract_data(self) -> dict:
        """
        Constructs a dictionary containing key contract details for IB API.

        Returns:
            Dict[str, str]: A dictionary with details such as symbol, security type, currency, exchange, and multiplier.
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
        Creates an IB API `Contract` object using the symbol's details.

        Returns:
            Contract: A fully initialized `Contract` object.

        Raises:
            Exception: If an error occurs during contract creation.
        """
        try:
            contract_data = self.to_contract_data()
            contract = Contract()
            for key, value in contract_data.items():
                setattr(contract, key, value)
            return contract
        except Exception as e:
            raise Exception(f"Unexpected error during Contract creation: {e}")

    def to_dict(self) -> dict:
        """
        Converts the symbol into a dictionary representation.

        Returns:
            Dict[str, str]: A dictionary containing `ticker` and `security_type`.
        """
        return {
            "ticker": self.midas_ticker,
            "security_type": self.security_type.value,
        }

    def commission_fees(self, quantity: float) -> float:
        """
        Calculates commission fees for a given order quantity.

        Args:
            quantity (float): The quantity of the order.

        Returns:
            float: Commission fees as a negative value to reflect cost.
        """
        return abs(quantity) * self.fees * -1

    def slippage_price(self, current_price: float, action: Action) -> float:
        """
        Adjusts the current price based on the slippage factor and order action.

        Args:
            current_price (float): The current market price of the symbol.
            action (Action): The action performed (LONG, SHORT, etc.).

        Returns:
            float: Adjusted price after accounting for slippage.

        Raises:
            ValueError: If the action is invalid or not an `Action` enum.
        """
        if action in [Action.LONG, Action.COVER]:  # Buying
            adjusted_price = current_price + self.slippage_factor
        elif action in [Action.SHORT, Action.SELL]:  # Selling
            adjusted_price = current_price - self.slippage_factor
        else:
            raise ValueError("'action' must be of type Action enum.")

        return adjusted_price

    def after_day_session(self, timestamp_ns: int) -> bool:
        """
        Checks if a given timestamp occurs after the day trading session.

        Args:
            timestamp_ns (int): Timestamp in nanoseconds.

        Returns:
            bool: True if the timestamp is after the session close time.
        """
        dt = datetime.fromisoformat(
            unix_to_iso(timestamp_ns, tz_info="America/New_York")
        )
        time = dt.time()

        if self.trading_sessions.day_close < time:
            return True
        return False

    def in_day_session(self, timestamp_ns: int) -> bool:
        """
        Checks if a given timestamp occurs during the day trading session.

        Args:
            timestamp_ns (int): Timestamp in nanoseconds.

        Returns:
            bool: True if the timestamp falls within the session open and close times.
        """
        dt = datetime.fromisoformat(
            unix_to_iso(timestamp_ns, tz_info="America/New_York")
        )
        # time = dt.time()

        return (
            self.trading_sessions.day_open
            <= dt.time()
            <= self.trading_sessions.day_close
        )

    @abstractmethod
    def value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Abstract method to calculate the total value of a position.

        Args:
            quantity (float): The quantity of the position.
            price (Optional[float]): Market price for the position (optional).

        Returns:
            float: Total value of the position.
        """
        pass

    @abstractmethod
    def cost(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Abstract method to calculate the total cost of a position.

        Args:
            quantity (float): The quantity of the position.
            price (Optional[float]): Market price for the position (optional).

        Returns:
            float: Total cost of the position.
        """
        pass


@dataclass
class Equity(Symbol):
    """
    Represents an equity (stock) financial instrument.

    Attributes:
        instrument_id (int): Unique identifier for the equity.
        broker_ticker (str): Ticker symbol used by the broker.
        data_ticker (str): Ticker symbol for market data feeds.
        midas_ticker (str): Internal system ticker name.
        security_type (SecurityType): Type of security (set to STOCK for equities).
        currency (Currency): Currency in which the equity trades.
        exchange (Venue): Trading venue or exchange where the equity is listed.
        fees (float): Transaction fees for the equity.
        initial_margin (float): Margin requirement for the equity.
        quantity_multiplier (int): Scaling factor for quantity.
        price_multiplier (float): Scaling factor for price.
        trading_sessions (TradingSession): Trading session times for the equity.
        slippage_factor (float): Slippage adjustment factor.
        company_name (str): The name of the company issuing the equity.
        industry (Industry): The industry to which the company belongs.
        market_cap (float): The market capitalization of the company.
        shares_outstanding (int): Total number of shares outstanding for the equity.
        contract (Contract): IB API Contract object (generated during initialization).
    """

    company_name: str
    industry: Industry
    market_cap: float
    shares_outstanding: int

    def __post_init__(self):
        """
        Post-initialization setup for the Equity class.

        - Sets the security type to `STOCK`.
        - Performs type validation on attributes.
        - Generates an IB API Contract object for the equity.

        Raises:
            TypeError: If any attribute has an invalid type.
        """
        self.security_type = SecurityType.STOCK
        super().__post_init__()

        # Type checks
        if not isinstance(self.company_name, str):
            raise TypeError("'company_name' must be of type str.")
        if not isinstance(self.industry, Industry):
            raise TypeError("'industry' must be of type Industry.")
        if not isinstance(self.market_cap, float):
            raise TypeError("'market_cap' must be of type float.")
        if not isinstance(self.shares_outstanding, int):
            raise TypeError("'shares_outstanding' must be of type int.")

        # Create contract object
        self.contract = self.to_contract()

    def to_contract_data(self) -> dict:
        """
        Constructs a dictionary containing key contract details for the equity.

        Returns:
            dict: Contract data including broker ticker, security type, currency, exchange, and multiplier.
        """
        data = super().to_contract_data()
        return data

    def to_dict(self) -> dict:
        """
        Converts the Equity object to a dictionary representation.

        Returns:
            dict: A dictionary containing:
                - Ticker details.
                - Symbol-specific data including company name, venue, currency, industry, market cap, and shares outstanding.
        """
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
        Calculates the total value of a position in the equity.

        Args:
            quantity (float): The number of shares held.
            price (float): The market price of the equity.

        Returns:
            float: The calculated total value of the equity position.
        """
        return quantity * price

    def cost(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculates the total cost of acquiring or holding a position in the equity.

        Args:
            quantity (float): The number of shares held or acquired.
            price (float): The market price of the equity.

        Returns:
            float: The calculated cost of the equity position.
        """
        return abs(quantity) * price


@dataclass
class Future(Symbol):
    """
    Represents a futures contract traded on an exchange.

    Attributes:
        instrument_id (int): Unique numeric identifier for the instrument.
        broker_ticker (str): Ticker symbol used by the broker.
        data_ticker (str): Ticker symbol used for data sources (e.g., market data feeds).
        midas_ticker (str): Internal ticker name for the system.
        security_type (SecurityType): Type of security (e.g., STOCK, OPTION, FUTURE).
        currency (Currency): Currency in which the instrument trades.
        exchange (Venue): Trading venue or exchange where the symbol is listed.
        fees (float): Transaction fees (e.g., commission) per unit traded.
        initial_margin (float): Margin required per unit of the instrument.
        quantity_multiplier (int): Scaling factor for quantity (e.g., lot size, contract size).
        price_multiplier (float): Scaling factor for price (e.g., futures multipliers).
        trading_sessions (TradingSession): Time window(s) for when the symbol is tradable.
        slippage_factor (float): Adjustment factor to simulate slippage in price.
        product_code (str): Unique code identifying the futures product.
        product_name (str): Name of the futures product.
        industry (Industry): The industry to which the futures product belongs.
        contract_size (float): The size of a single futures contract.
        contract_units (ContractUnits): The unit of measurement for the futures contract.
        tick_size (float): The minimum price movement of the contract.
        min_price_fluctuation (float): The minimum price fluctuation for the futures contract.
        continuous (bool): Whether the futures contract is continuous (rolls over automatically).
        lastTradeDateOrContractMonth (str): Last trade date or contract month for the futures product.
        expr_months (List[FuturesMonth]): List of eligible expiration months for the futures product.
        term_day_rule (str): Rule defining the termination or expiration day.
        market_calendar (str): Calendar used for determining trading days.
        contract (Contract): Interactive Brokers API `Contract` object (created post-init).
    """

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
        """
        Post-initialization method for validating attributes and generating the contract object.

        Raises:
            TypeError: If any attribute fails type validation.
            ValueError: If tick size is invalid or other constraints are not met.
        """
        self.security_type = SecurityType.FUTURE
        super().__post_init__()

        # Type checks
        if not isinstance(self.product_code, str):
            raise TypeError("'product_code' must be of type str.")
        if not isinstance(self.product_name, str):
            raise TypeError("'product_name' must be of type str.")
        if not isinstance(self.industry, Industry):
            raise TypeError("'industry' must be of type Industry.")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError("'contract_size' must be of type int or float.")
        if not isinstance(self.contract_units, ContractUnits):
            raise TypeError("'contract_units' must be of type ContractUnits.")
        if not isinstance(self.tick_size, (int, float)):
            raise TypeError("'tick_size' must be of type int or float.")
        if not isinstance(self.min_price_fluctuation, (int, float)):
            raise TypeError("'min_price_fluctuation' must be int or float.")
        if not isinstance(self.continuous, bool):
            raise TypeError("'continuous' must be of type boolean.")
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError("'lastTradeDateOrContractMonth' must be a string.")
        for month in self.expr_months:
            if not isinstance(month, FuturesMonth):
                raise TypeError("'expr_month' must be list of FuturesMonth.")
        if not isinstance(self.term_day_rule, str):
            raise TypeError("'term_day_rule' must be of type str.")

        # Constraint Checks
        if self.tick_size <= 0:
            raise ValueError("'tickSize' must be greater than zero.")

        # Create contract object
        self.contract = self.to_contract()

    def to_contract_data(self) -> dict:
        """
        Generates contract data required for trading or IB API.

        Returns:
            dict: A dictionary with contract-specific attributes including last trade date.
        """
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = (
            self.lastTradeDateOrContractMonth
        )
        return data

    def to_dict(self) -> dict:
        """
        Converts the Future object to a dictionary representation.

        Returns:
            dict: A dictionary containing futures-specific and base symbol details.
        """
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
        Calculate the total value of the futures position.

        Args:
            quantity (float): Number of contracts.
            price (float): Price per contract.

        Returns:
            float: The total position value.
        """
        if price is None:
            raise ValueError("'price' cannot be None when calculating value.")
        return (
            self.price_multiplier * price * quantity * self.quantity_multiplier
        )

    def cost(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the cost or margin requirement for the position.

        Args:
            quantity (float): Number of contracts.
            price (Optional[float]): Price per contract (not used for cost calculation).

        Returns:
            float: The total margin requirement.
        """
        return abs(quantity) * self.initial_margin

    def in_rolling_window(
        self,
        ts: int,
        window: int = 2,
        tz_info="UTC",
    ) -> bool:
        """
        Check if the given timestamp is within a rolling window near the contract's termination date.

        Args:
            ts (int): Timestamp in nanoseconds.
            window (int): Rolling window size in days (default is 2).
            tz_info (str): Timezone info (default is "UTC").

        Returns:
            bool: True if within the rolling window, False otherwise.
        """

        # Convert the timestamp into a datetime object
        event_date = unix_to_date(ts, tz_info)
        year, month = event_date.year, event_date.month

        if month in [month.value for month in self.expr_months]:
            # Get the termination date for the current contract month/year
            termination_date = self.apply_day_rule(month, year).date()

            # Calculate the rolling window period
            window_start = termination_date - timedelta(days=window)
            window_end = termination_date + timedelta(days=window)

            # Check if the event date falls within the rolling window
            return window_start <= event_date <= window_end
        return False

    def apply_day_rule(self, month: int, year: int) -> datetime:
        """
        Determine the contract expiration date based on the termination day rule.

        Args:
            month (int): Expiration month.
            year (int): Expiration year.

        Returns:
            datetime: Expiration date as per the rule.

        Raises:
            ValueError: If the termination rule is invalid.
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
        Retrieve the nth business day of a specified month and year.

        Args:
            month (int): The target month (1-12).
            year (int): The target year.
            nth_day (int): The business day to retrieve (e.g., 1st, 2nd, etc.).
            market_calendar (str): The trading calendar name (e.g., 'NYSE', 'CME').

        Returns:
            datetime: The date corresponding to the nth business day.

        Raises:
            IndexError: If `nth_day` exceeds the number of business days in the month.
            ValueError: If invalid calendar name is provided.
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
        Retrieve the nth last business day of a specified month and year.

        Args:
            month (int): The target month (1-12).
            year (int): The target year.
            nth_last_day (int): The business day to retrieve, counting from the end (e.g., 1 = last).
            market_calendar (str): The trading calendar name (e.g., 'NYSE', 'CME').

        Returns:
            datetime: The date corresponding to the nth last business day.

        Raises:
            IndexError: If `nth_last_day` exceeds the total business days in the month.
            ValueError: If invalid calendar name is provided.
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
        Retrieve the nth business day before a specified target day within a given month and year.

        Args:
            month (FuturesMonth): The target month as a FuturesMonth enum.
            year (int): The target year.
            target_day (int): The target day of the month (e.g., 15 for the 15th day).
            nth_day (int): The number of business days before the target day.
            market_calendar (str): The trading calendar name (e.g., 'NYSE', 'CME').

        Returns:
            datetime: The date corresponding to the nth business day before the target day.

        Raises:
            IndexError: If the calculated business day does not exist.
            ValueError: If invalid calendar name or parameters are provided.
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
    """
    Represents an Option contract as a financial instrument.

    This class extends the Symbol class and includes option-specific attributes such as
    strike price, expiration date, and option type.

    Attributes:
        instrument_id (int): Unique identifier for the equity.
        broker_ticker (str): Ticker symbol used by the broker.
        data_ticker (str): Ticker symbol for market data feeds.
        midas_ticker (str): Internal system ticker name.
        security_type (SecurityType): Type of security (set to STOCK for equities).
        currency (Currency): Currency in which the equity trades.
        exchange (Venue): Trading venue or exchange where the equity is listed.
        fees (float): Transaction fees for the equity.
        initial_margin (float): Margin requirement for the equity.
        quantity_multiplier (int): Scaling factor for quantity.
        price_multiplier (float): Scaling factor for price.
        trading_sessions (TradingSession): Trading session times for the equity.
        slippage_factor (float): Slippage adjustment factor.
        company_name (str): The name of the company issuing the equity.
        industry (Industry): The industry to which the company belongs.
        market_cap (float): The market capitalization of the company.
        shares_outstanding (int): Total number of shares outstanding for the equity.
        strike_price (float): The strike price at which the option can be exercised.
        expiration_date (str): The expiration date of the option in YYYY-MM-DD format.
        option_type (Right): The type of option, either CALL or PUT.
        contract_size (int): The number of underlying units per contract.
        underlying_name (str): The name of the underlying asset.
        lastTradeDateOrContractMonth (str): The last trade date or contract month of the option.
        contract (Contract): IB API Contract object (generated during initialization).
    """

    strike_price: float
    expiration_date: str
    option_type: Right
    contract_size: int
    underlying_name: str
    lastTradeDateOrContractMonth: str

    def __post_init__(self):
        """
        Validates the Option fields and initializes the contract object.

        Raises:
            TypeError: If any field does not match its expected type.
            ValueError: If 'strike_price' is less than or equal to zero.
        """
        self.security_type = SecurityType.OPTION
        super().__post_init__()

        # Type checks
        if not isinstance(self.strike_price, (int, float)):
            raise TypeError("'strike_price' must be of type int or float.")
        if not isinstance(self.expiration_date, str):
            raise TypeError("'expiration_date' must be of type str.")
        if not isinstance(self.option_type, Right):
            raise TypeError("'option_type' must be of type Right.")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError("'contract_size' must be of type int or float.")
        if not isinstance(self.underlying_name, str):
            raise TypeError("'underlying_name' must be of type str.")
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError("'lastTradeDateOrContractMonth' must be a string.")

        # Constraint checks
        if self.strike_price <= 0:
            raise ValueError("'strike' must be greater than zero.")

        # Create contract object
        self.contract = self.to_contract()

    def to_contract_data(self) -> dict:
        """
        Constructs a dictionary representation for creating an IBKR Contract object.

        Returns:
            dict: A dictionary containing option-specific contract details such as strike price,
                  expiration date, and option type, in addition to base contract details.
        """
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = (
            self.lastTradeDateOrContractMonth
        )
        data["right"] = self.option_type.value
        data["strike"] = self.strike_price
        return data

    def to_dict(self) -> dict:
        """
        Constructs a dictionary representation of the Option object.

        Returns:
            dict: A dictionary containing the option details including strike price, expiration,
                  option type, and other metadata.
        """
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
        Calculate the total market value of the option position.

        Args:
            quantity (float): The number of contracts held.
            price (Optional[float]): The premium price of the option.

        Returns:
            float: The calculated market value of the option position.

        Raises:
            ValueError: If `price` is not provided.
        """
        if price is None:
            raise ValueError("Price must be provided to calculate value.")
        return abs(quantity) * price * self.quantity_multiplier

    def cost(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the cost to acquire or maintain the option position.

        Args:
            quantity (float): The number of contracts to be traded.
            price (Optional[float]): The premium price of the option.

        Returns:
            float: The total cost to acquire the option position.

        Raises:
            ValueError: If `price` is not provided.
        """
        if price is None:
            raise ValueError("Price must be provided to calculate cost.")

        return abs(quantity) * price * self.quantity_multiplier


class SymbolFactory:
    """
    A factory class to create Symbol objects from a dictionary.

    This class supports parsing and mapping symbol attributes, including time strings,
    enumerated fields, and trading sessions. It dynamically determines the appropriate
    Symbol subclass to instantiate (e.g., Equity, Future, Option).
    """

    @classmethod
    def _get_symbol_class(cls, symbol_type: str):
        """
        Get the appropriate Symbol subclass based on the provided symbol type.

        Args:
            symbol_type (str): The type of symbol (e.g., "Equity", "Future", "Option").

        Returns:
            Type[Symbol]: The corresponding Symbol subclass.

        Raises:
            ValueError: If the provided symbol type is not recognized.
        """
        if symbol_type == "Equity":
            return Equity
        elif symbol_type == "Future":
            return Future
        elif symbol_type == "Option":
            return Option
        else:
            raise ValueError(f"Unknown symbol type: {symbol_type}")

    @classmethod
    def _parse_time(cls, time_str: str) -> time:
        """
        Parse a time string in 'HH:MM' format into a time object.

        Args:
            time_str (str): The time string to parse.

        Returns:
            time: The parsed time object.

        Example:
            >>> SymbolFactory._parse_time("09:30")
            datetime.time(9, 30)
        """
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)

    @classmethod
    def _map_symbol_enum_fields(cls, symbol_data: dict) -> dict:
        """
        Map string values in symbol data to their respective Enum types.

        Args:
            symbol_data (dict): The dictionary containing raw symbol data.

        Returns:
            dict: A dictionary with enum fields mapped to their corresponding Enum values.
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
        Create a Symbol object from a dictionary.

        Args:
            symbol_data (dict): A dictionary containing symbol attributes.

        Returns:
            Symbol: An instance of the appropriate Symbol subclass (Equity, Future, or Option).

        Raises:
            ValueError: If the symbol type is not recognized.

        Example:
            >>> symbol_data = {
                    "type": "Equity",
                    "currency": "USD",
                    "security_type": "STOCK",
                    "exchange": "NASDAQ",
                    "trading_sessions": {"day_open": "09:30", "day_close": "16:00"}
                }
            >>> symbol = SymbolFactory.from_dict(symbol_data)
            >>> type(symbol)
            <class 'Equity'>
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
    """
    A mapping class to manage Symbol objects by their universal instrument IDs and associated tickers.

    This class allows retrieval, addition, and management of Symbol objects based on
    various tickers (broker, data, midas) or instrument IDs.
    """

    def __init__(self):
        """
        Initialize the SymbolMap with dictionaries to map instrument IDs and tickers to Symbol objects.
        """
        # Maps the instrument ID to the Symbol object
        self.map: Dict[int, Symbol] = {}

        # Maps broker/data/midas tickers to instrument IDs
        self.broker_map: Dict[str, int] = {}
        self.data_map: Dict[str, int] = {}
        self.midas_map: Dict[str, int] = {}

    def add_symbol(self, symbol: Symbol) -> None:
        """
        Add a Symbol object to the map.

        Args:
            symbol (Symbol): The Symbol object to add.

        Example:
            >>> equity_symbol = Equity(...)
            >>> symbol_map = SymbolMap()
            >>> symbol_map.add_symbol(equity_symbol)
        """
        # Map the tickers to the instrument ID
        self.broker_map[symbol.broker_ticker] = symbol.instrument_id
        self.data_map[symbol.data_ticker] = symbol.instrument_id
        self.midas_map[symbol.midas_ticker] = symbol.instrument_id

        # Associate the instrument ID with the symbol
        self.map[symbol.instrument_id] = symbol

    def get_symbol(self, ticker: str) -> Symbol:
        """
        Retrieve the Symbol object associated with a given ticker.

        Args:
            ticker (str): The ticker (broker, data, or midas) to look up.

        Returns:
            Symbol: The associated Symbol object, or None if not found.

        Example:
            >>> symbol = symbol_map.get_symbol("AAPL")
        """
        instrument_id = self.get_id(ticker)
        return self.map.get(instrument_id)

    def get_id(self, ticker: str) -> int:
        """
        Retrieve the instrument ID associated with a given ticker.

        Args:
            ticker (str): The ticker to look up.

        Returns:
            int: The instrument ID, or None if not found.
        """
        instrument_id = (
            self.broker_map.get(ticker)
            or self.data_map.get(ticker)
            or self.midas_map.get(ticker)
        )
        return instrument_id

    @property
    def symbols(self) -> List[Symbol]:
        """
        Retrieve all unique Symbol objects.

        Returns:
            List[Symbol]: A list of all Symbol objects in the map.
        """
        return list(self.map.values())

    @property
    def instrument_ids(self) -> List[int]:
        """
        Retrieve all unique instrument IDs.

        Returns:
            List[int]: A list of all instrument IDs.
        """
        return list(self.map.keys())

    @property
    def broker_tickers(self) -> List[str]:
        """
        Retrieve all broker tickers.

        Returns:
            List[str]: A list of all broker tickers.
        """
        return list(self.broker_map.keys())

    @property
    def data_tickers(self) -> List[str]:
        """
        Retrieve all data provider tickers.

        Returns:
            List[str]: A list of all data provider tickers.
        """
        return list(self.data_map.keys())

    @property
    def midas_tickers(self) -> List[str]:
        """
        Retrieve all Midas tickers.

        Returns:
            List[str]: A list of all Midas tickers.
        """
        return list(self.midas_map.keys())

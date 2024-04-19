from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal

# -- Symbol Details --
class AssetClass(Enum):
    EQUITY = 'EQUITY'
    COMMODITY = 'COMMODITY'
    FIXED_INCOME ='FIXED_INCOME'
    FOREX='FOREX'
    CRYPTOCURRENCY='CRYPTOCURRENCY'
    
class SecurityType(Enum):
    STOCK = 'STOCK'
    FUTURE = 'FUTURE'
    OPTION = 'OPTION'
    INDEX = 'INDEX'

class Venue(Enum):   
    NASDAQ = 'NASDAQ'
    CME = 'CME'     
    CBOT='CBOT'
    NYSE="NYSE"
              
class Currency(Enum):   
    USD='USD'
    CAD='CAD'   
    EUR='EUR'
    GBP='GBP'
    AUD='AUD'           
    JPY='JPY'

class Industry(Enum):
    # Equities
    ENERGY='Energy'
    MATERIALS='Materials'
    INDUSTRIALS='Industrials'
    UTILITIES='Utilities'
    HEALTHCARE='Healthcare'
    FINANCIALS='Financials'
    CONSUMER='Consumer'
    TECHNOLOGY='Technology'
    COMMUNICATION='Communication'
    REAL_ESTATE='Real Estate'   
    
    # Commodities
    METALS='Metals' 
    AGRICULTURE='Agriculture'
    #ENERGY         

class ContractUnits(Enum):
    BARRELS='Barrels'
    BUSHELS='Bushels'
    POUNDS='Pounds'
    TROY_OUNCE='Troy Ounce'
    METRIC_TON='Metric Ton'
    SHORT_TON='Short Ton'


# -- Symbols -- 
@dataclass
class Symbol:
    ticker: str
    security_type: SecurityType

    def __post_init__(self):
        # Type checks
        if not isinstance(self.ticker, str):
            raise TypeError("ticker must be of type str")
        if not isinstance(self.security_type, SecurityType):
            raise TypeError("security_type must be of type SecurityType.")
    
    def to_dict(self):
        return {
            'ticker': self.ticker,
            'security_type': self.security_type.value  # Assuming security_type is an enum or similar
        }

@dataclass
class Equity(Symbol):
    company_name: str
    venue: Venue
    currency: Currency
    industry: Industry
    market_cap: float
    shares_outstanding: int

    def __post_init__(self):
        super().__post_init__()  # Call to check types in superclass
        # Additional type checks
        if not isinstance(self.company_name, str):
            raise TypeError("company_name must be of type str")
        if not isinstance(self.venue, Venue):
            raise TypeError("venue must be of type Venue.")
        if not isinstance(self.currency, Currency):
            raise TypeError("currency must be of type Currency.")
        if not isinstance(self.industry, Industry):
            raise TypeError("industry must be of type Industry.")
        if not isinstance(self.market_cap, float):
            raise TypeError("market_cap must be of type float.")
        if not isinstance(self.shares_outstanding, int):
            raise TypeError("shares_outstanding must be of type int.")
    
    def to_dict(self):
        symbol_dict = super().to_dict()  # Properly call the superclass to_dict
        symbol_dict ["symbol_data"]= {
            'company_name': self.company_name,
            'venue': self.venue.value,  # Make sure venue is correctly serialized
            'currency': self.currency.value,  # Same for currency
            'industry': self.industry.value,  # And industry
            'market_cap': self.market_cap,
            'shares_outstanding': self.shares_outstanding
        }
        return symbol_dict
    
@dataclass
class Future(Symbol):
    product_code: str
    product_name: str
    venue: Venue
    currency: Currency
    industry: Industry
    contract_size: float
    contract_units: ContractUnits
    tick_size: float
    min_price_fluctuation: float
    continuous: bool

    def __post_init__(self):
        super().__post_init__()  # Call to check types in superclass
        # Additional type checks
        if not isinstance(self.product_code, str):
            raise TypeError("product_code must be of type str")
        if not isinstance(self.product_name, str):
            raise TypeError("product_name must be of type str")
        if not isinstance(self.venue, Venue):
            raise TypeError("venue must be of type Venue.")
        if not isinstance(self.currency, Currency):
            raise TypeError("currency must be of type Currency.")
        if not isinstance(self.industry, Industry):
            raise TypeError("industry must be of type Industry.")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError("contract_size must be of type int or float.")
        if not isinstance(self.contract_units, ContractUnits):
            raise TypeError("contract_units must be of type ContractUnits.")
        if not isinstance(self.tick_size, (int, float)):
            raise TypeError("tick_size must be of type int or float.")
        if not isinstance(self.min_price_fluctuation, (int, float)):
            raise TypeError("min_price_fluctuation must be of type int or float.")
        if not isinstance(self.continuous, bool):
            raise TypeError("continuous must be of type boolean.")
    
    def to_dict(self):
        symbol_dict = super().to_dict()  # Properly call the superclass to_dict
        symbol_dict ["symbol_data"]= {
            'product_code': self.product_code,
            'product_name':  self.product_name,
            'venue':  self.venue.value,
            'currency': self.currency.value,
            'industry': self.industry.value,
            'contract_size': self.contract_size,
            'contract_units': self.contract_units.value,
            'tick_size': self.tick_size,
            'min_price_fluctuation' : self.min_price_fluctuation,
            'continuous' : self.continuous
        }
        return symbol_dict

@dataclass
class Option(Symbol):
    strike_price: float
    currency: Currency
    venue: Venue
    expiration_date: str
    option_type: str
    contract_size: int
    underlying_name: str

    def __post_init__(self):
        super().__post_init__()  # Call to check types in superclass
        # Additional type checks
        if not isinstance(self.strike_price, (int, float)):
            raise TypeError("strike_price must be of type int or float")
        if not isinstance(self.currency, Currency):
            raise TypeError("currency must be of type Currency.")
        if not isinstance(self.venue, Venue):
            raise TypeError("venue must be of type Venue.")
        if not isinstance(self.expiration_date, str):
            raise TypeError("expiration_date must be of type str")
        if not isinstance(self.option_type, str):
            raise TypeError("option_type must be of type str")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError("contract_size must be of type int or float")
        if not isinstance(self.underlying_name, str):
            raise TypeError("underlying_name must be of type str")
    
    def to_dict(self):
        symbol_dict = super().to_dict()  # Properly call the superclass to_dict
        symbol_dict ["symbol_data"]= {
            'strike_price': self.strike_price,
            'currency': self.currency.value, 
            'venue': self.venue.value,
            'expiration_date': self.expiration_date,
            'option_type': self.option_type,
            'contract_size': self.contract_size,
            'underlying_name':self.underlying_name
        }
        return symbol_dict

@dataclass
class Index(Symbol):
    name: str
    currency: Currency
    asset_class: AssetClass
    venue: Venue

    def __post_init__(self):
        super().__post_init__()  # Call to check types in superclass
        # Additional type checks
        if not isinstance(self.name, str):
            raise TypeError("name must be of type str")
        if not isinstance(self.currency, Currency):
            raise TypeError("currency must be of type Currency.")
        if not isinstance(self.asset_class, AssetClass):
            raise TypeError("asset_class must be of type AssetClass.")
        if not isinstance(self.venue, Venue):
            raise TypeError("venue must be of type Venue.")
    
    def to_dict(self):
        symbol_dict = super().to_dict()  # Properly call the superclass to_dict
        symbol_dict ["symbol_data"]= {
            'name': self.name,
            'currency': self.currency.value,
            'asset_class': self.asset_class.value,
            'venue': self.venue.value
        }
        return symbol_dict

# -- Market Data --
@dataclass
class BarData:
    ticker: str
    timestamp: str
    open: Decimal
    close: Decimal
    high: Decimal
    low: Decimal
    volume: int

    def __post_init__(self):
        # Type checks
        if not isinstance(self.ticker, str):
            raise TypeError("ticker must be of type str")        
        if not isinstance(self.timestamp, str):
            raise TypeError("timestamp must be of type str")
        if not isinstance(self.open, Decimal):
            raise TypeError("open must be of type Decimal.")
        if not isinstance(self.high, Decimal):
            raise TypeError("high must be of type Decimal.")
        if not isinstance(self.low, Decimal):
            raise TypeError("low must be of type Decimal.")
        if not isinstance(self.close, Decimal):
            raise TypeError("close must be of type Decimal.")
        if not isinstance(self.volume, int):
            raise TypeError("volume must be of type int.")
    
    def to_dict(self):
        return {
            "symbol": self.ticker,
            "timestamp": self.timestamp,
            "open": str(self.open),
            "close": str(self.close),
            "high": str(self.high),
            "low": str(self.low),
            "volume": self.volume
        }

@dataclass
class QuoteData:
    ticker: str
    timestamp: str
    ask: Decimal
    ask_size: Decimal
    bid: Decimal
    bid_size: Decimal

    def __post_init__(self):
        # Type checks
        if not isinstance(self.ticker, str):
            raise TypeError("ticker must be of type str")   
        if not isinstance(self.timestamp, str):
            raise TypeError(f"timestamp must be of type str")
        if not isinstance(self.ask, Decimal):
            raise TypeError(f"'ask' must be of type Decimal")
        if not isinstance(self.ask_size, Decimal):
            raise TypeError(f"'ask_size' must be of type Decimal")
        if not isinstance(self.bid, Decimal):
            raise TypeError(f"'bid' must be of type Decimal")
        if not isinstance(self.bid_size, Decimal):
            raise TypeError(f"'bid_size' must be of type Decimal")
        
        # Constraint checks
        if self.ask <= 0:
            raise ValueError(f"'ask' must be greater than zero")
        if self.ask_size <= 0:
            raise ValueError(f"'ask_size' must be greater than zero")
        if self.bid <= 0:
            raise ValueError(f"'bid' must be greater than zero")
        if self.bid_size <= 0:
            raise ValueError(f"'bid_size' must be greater than zero")
        
    def to_dict(self):
        return {
            "ticker": self.ticker,
            "timestamp": self.timestamp,
            "ask": self.ask,
            "ask_size": self.ask_size,
            "bid": self.bid,
            "bid_size": self.bid_size 
        }


# -- Backtest & Trading Sessions
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
    
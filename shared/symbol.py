# shared/symbol.py
from enum import Enum
from typing import Optional
from ibapi.contract import Contract
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

# -- Symbol Details --
class AssetClass(Enum):
    EQUITY = 'EQUITY'
    COMMODITY = 'COMMODITY'
    FIXED_INCOME ='FIXED_INCOME'
    FOREX='FOREX'
    CRYPTOCURRENCY='CRYPTOCURRENCY'
    
class SecurityType(Enum):
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    CRYPTO = "CRYPTO"
    INDEX = "IND"
    BOND ="BOND"
    # ['STK', 'CMDTY','FUT','OPT','CASH','CRYPTO','FIGI','IND','CFD','FOP','BOND'] 

class Venue(Enum):   
    NASDAQ = 'NASDAQ'
    NYSE="NYSE"
    CME = 'CME'     
    CBOT='CBOT'
    CBOE = "CBOE"
    COMEX = "COMEX"
    GLOBEX = "GLOBEX"
    NYMEX = "NYMEX"
    INDEX="INDEX" # specific for the creeation of indexes
    # IB specific
    SMART = "SMART"
    ISLAND = "ISLAND"
              
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

class Right(Enum):
    CALL = "CALL"
    PUT = "PUT"

# -- Symbols -- 
@dataclass
class Symbol:
    ticker: str = None
    security_type: SecurityType = None
    currency: Currency = None
    exchange: Venue = None
    fees: float = None
    initialMargin: float = None
    quantity_multiplier: int = None
    price_multiplier: float = None
    data_ticker: Optional[str] = None
    contract: Contract = field(init=False)

    def __post_init__(self):
        # Type Validation
        if not isinstance(self.ticker, str):
            raise TypeError(f"ticker must be of type str")
        if not isinstance(self.security_type, SecurityType):
            raise TypeError(f"security_type must be of type SecurityType.")
        if not isinstance(self.currency, Currency):
            raise TypeError(f"currency must be enum instance Currency")
        if not isinstance(self.exchange, Venue):
            raise TypeError(f"exchange must be enum instance Venue")
        if not isinstance(self.fees,(float, int)):
            raise TypeError(f"fees must be int or float")
        if not isinstance(self.initialMargin, (float,int)):
            raise TypeError(f"initialMargin must be an int or float")
        if not isinstance(self.quantity_multiplier, (float,int)):
            raise TypeError(f"quantity_multiplier must be of type int or float")
        if not isinstance(self.price_multiplier, (float, int)):
            raise TypeError(f"price_multiplier must be of type int or float")
        if self.data_ticker is not None and not isinstance(self.data_ticker, str):
            raise TypeError(f"data_ticker must be a string or None")

        # Constraint Validation
        if self.fees < 0:
            raise ValueError(f"fees cannot be negative")
        if self.initialMargin < 0:
            raise ValueError(f"initialMargin must be non-negative")
        if self.price_multiplier <= 0:
            raise ValueError(f"price_multiplier must be greater than 0")
        if self.quantity_multiplier <= 0:
            raise ValueError(f"quantity_multiplier must be greater than 0")

        # Logic
        if not self.data_ticker:
            self.data_ticker = self.ticker

        self.contract = self.to_contract()
    
    def to_contract_data(self) -> dict:
        return {
            "symbol": self.ticker,
            "secType": self.security_type.value,
            "currency": self.currency.value,
            "exchange": self.exchange.value, 
            "multiplier":self.quantity_multiplier
            }
    
    def to_contract(self) -> Contract:
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
            'ticker': self.ticker,
            'security_type': self.security_type.value  # Assuming security_type is an enum or similar
        }

@dataclass
class Equity(Symbol):
    company_name: str =None
    industry: Industry = None
    market_cap: float = None
    shares_outstanding: int = None
    security_type: SecurityType = SecurityType.STOCK

    def __post_init__(self):
        # Additional type checks
        if not isinstance(self.company_name, str):
            raise TypeError("company_name must be of type str")
        if not isinstance(self.industry, Industry):
            raise TypeError("industry must be of type Industry.")
        if not isinstance(self.market_cap, float):
            raise TypeError("market_cap must be of type float.")
        if not isinstance(self.shares_outstanding, int):
            raise TypeError("shares_outstanding must be of type int.")
        
        super().__post_init__()  # Call to check types in superclass

    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        return data
    
    def to_dict(self):
        symbol_dict = super().to_dict()  # Properly call the superclass to_dict
        symbol_dict ["symbol_data"]= {
            'company_name': self.company_name,
            'venue': self.exchange.value,  # Make sure venue is correctly serialized
            'currency': self.currency.value,  # Same for currency
            'industry': self.industry.value,  # And industry
            'market_cap': self.market_cap,
            'shares_outstanding': self.shares_outstanding
        }
        return symbol_dict
    
@dataclass
class Future(Symbol):
    product_code: str = None
    product_name: str = None
    industry: Industry = None
    contract_size: float = None
    contract_units: ContractUnits = None
    tick_size: float = None
    min_price_fluctuation: float = None
    continuous: bool = None
    lastTradeDateOrContractMonth: str = None
    security_type: SecurityType = SecurityType.FUTURE    

    def __post_init__(self):
        # Additional type checks
        if not isinstance(self.product_code, str):
            raise TypeError("product_code must be of type str")
        if not isinstance(self.product_name, str):
            raise TypeError("product_name must be of type str")
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
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError(f"lastTradeDateOrContractMonth must be a string")

        super().__post_init__()  # Call to check types in superclass
        
        # Constraint Validation
        if self.tick_size <= 0:
            raise ValueError(f"tickSize must be greater than 0")
        # if self.multiplier <= 0:
        #     raise ValueError(f"multiplier must be greater than 0")
        # if self.initialMargin <= 0:
        #     raise ValueError(f"initialMargin must be greater than 0")

    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = self.lastTradeDateOrContractMonth
        # data['multiplier'] = self.multiplier
        return data

    
    def to_dict(self):
        symbol_dict = super().to_dict()  # Properly call the superclass to_dict
        symbol_dict ["symbol_data"]= {
            'product_code': self.product_code,
            'product_name':  self.product_name,
            'venue':  self.exchange.value,
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
    strike_price: float = None
    expiration_date: str = None
    option_type: Right = None
    contract_size: int = None
    underlying_name: str = None
    lastTradeDateOrContractMonth: str = None
    security_type: SecurityType = SecurityType.OPTION

    def __post_init__(self):
        # Additional type checks
        if not isinstance(self.strike_price, (int, float)):
            raise TypeError("strike_price must be of type int or float")
        if not isinstance(self.expiration_date, str):
            raise TypeError("expiration_date must be of type str")
        if not isinstance(self.option_type,  Right):
            raise TypeError("option_type must be of type Right")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError("contract_size must be of type int or float")
        if not isinstance(self.underlying_name, str):
            raise TypeError("underlying_name must be of type str")
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError(f"lastTradeDateOrContractMonth must be a string")
        
        # Constraint Validation
        if self.strike_price <= 0:
            raise ValueError(f"strike must be greater than 0")
        # if self.multiplier <= 0:
        #     raise ValueError(f"multiplier must be greater than 0")

        super().__post_init__()  # Call to check types in superclass
    
    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = self.lastTradeDateOrContractMonth
        # data['multiplier'] = self.multiplier
        data["right"] = self.option_type.value  # Assuming Right is an Enum
        data["strike"] = self.strike_price
        return data
    
    def to_dict(self):
        symbol_dict = super().to_dict()  # Properly call the superclass to_dict
        symbol_dict ["symbol_data"]= {
            'strike_price': self.strike_price,
            'currency': self.currency.value, 
            'venue': self.exchange.value,
            'expiration_date': self.expiration_date,
            'option_type': self.option_type.value,
            'contract_size': self.contract_size,
            'underlying_name':self.underlying_name
        }
        return symbol_dict

@dataclass
class Index(Symbol):
    name: str = None
    asset_class: AssetClass = None
    
    # Don't need to set these -- overiding symbol --
    fees: float = 0.0
    initialMargin: float = 0.0
    quantity_multiplier: int = 1
    price_multiplier: float = 1.0
    exchange: Venue= Venue.INDEX
    security_type: SecurityType = SecurityType.INDEX


    def __post_init__(self):
        # Additional type checks
        if not isinstance(self.name, str):
            raise TypeError("name must be of type str")
        if not isinstance(self.asset_class, AssetClass):
            raise TypeError("asset_class must be of type AssetClass.")
        
        super().__post_init__()  # Call to check types in superclass
    
    def to_dict(self):
        symbol_dict = super().to_dict()  # Properly call the superclass to_dict
        symbol_dict ["symbol_data"]= {
            'name': self.name,
            'currency': self.currency.value,
            'asset_class': self.asset_class.value,
            'venue': self.exchange.value
        }
        return symbol_dict

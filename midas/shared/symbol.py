from enum import Enum
from typing import Optional
from ibapi.contract import Contract
from abc import ABC, abstractmethod
from midas.shared.orders import Action
from dataclasses import dataclass, field

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
    INDEX="INDEX"       # Specific for the creation of indexes
    SMART = "SMART"     # IB specific
    ISLAND = "ISLAND"   # IB specific
              
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
class Symbol(ABC):
    ticker: str = None
    security_type: SecurityType = None
    currency: Currency = None
    exchange: Venue = None
    fees: float = None
    initial_margin: float = None
    quantity_multiplier: int = None
    price_multiplier: float = None
    data_ticker: Optional[str] = None
    contract: Contract = field(init=False)
    slippage_factor:float = 0.0

    def __post_init__(self):
        # Type Validation
        if not isinstance(self.ticker, str):
            raise TypeError(f"'ticker' field must be of type str.")
        if not isinstance(self.security_type, SecurityType):
            raise TypeError(f"'security_type' field must be of type SecurityType.")
        if not isinstance(self.currency, Currency):
            raise TypeError(f"'currency' field must be enum instance Currency.")
        if not isinstance(self.exchange, Venue):
            raise TypeError(f"'exchange' field must be enum instance Venue.")
        if not isinstance(self.fees,(float, int)):
            raise TypeError(f"'fees' field must be int or float.")
        if not isinstance(self.initial_margin, (float,int)):
            raise TypeError(f"'initial_margin' field must be an int or float.")
        if not isinstance(self.quantity_multiplier, (float,int)):
            raise TypeError(f"'quantity_multiplier' field must be of type int or float.")
        if not isinstance(self.price_multiplier, (float, int)):
            raise TypeError(f"'price_multiplier' field must be of type int or float.")
        if not isinstance(self.slippage_factor, (float, int)):
            raise TypeError(f"'slippage_factor' field must be of type int or float.")
        if self.data_ticker is not None and not isinstance(self.data_ticker, str):
            raise TypeError(f"'data_ticker' field must be a string or None.")

        # Constraint Validation
        if self.fees < 0:
            raise ValueError(f"'fees' field cannot be negative.")
        if self.initial_margin < 0:
            raise ValueError(f"'initial_margin' field must be non-negative.")
        if self.price_multiplier <= 0:
            raise ValueError(f"'price_multiplier' field must be greater than zero.")
        if self.quantity_multiplier <= 0:
            raise ValueError(f"'quantity_multiplier' field must be greater than zero.")
        if self.slippage_factor < 0:
            raise ValueError(f"'slippage_factor' field must be greater than zero.")

        # Logic
        if not self.data_ticker:
            self.data_ticker = self.ticker
    
    def to_contract_data(self) -> dict:
        """ 
        Constructs a dictionary from instance variables used in the construction of Contract object.
        
        Returns:
        - dict : Representing the data to be added to Contract object.
        """
        return {
            "symbol": self.ticker,
            "secType": self.security_type.value,
            "currency": self.currency.value,
            "exchange": self.exchange.value, 
            "multiplier":self.quantity_multiplier
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
            'ticker': self.ticker,
            'security_type': self.security_type.value 
        }

    def commission_fees(self, quantity: float) -> float:
        """
        Calculates the commission fees for an order based on the quantity.

        Parameters:
        - quantity (float): The quantity of the order.

        Returns:
        - float: The calculated commission fees.
        """
        return abs(quantity) * self.fees

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
            raise ValueError(f"'action' must be of type Action enum.")
        
        return adjusted_price
    
    @abstractmethod
    def order_value(self, quantity: float, price: Optional[float] = None) -> float:
        pass
    
@dataclass
class Equity(Symbol):
    company_name: str =None
    industry: Industry = None
    market_cap: float = None
    shares_outstanding: int = None
    security_type: SecurityType = SecurityType.STOCK

    def __post_init__(self):
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
        symbol_dict ["symbol_data"]= {
            'company_name': self.company_name,
            'venue': self.exchange.value,  
            'currency': self.currency.value,  
            'industry': self.industry.value,  
            'market_cap': self.market_cap,
            'shares_outstanding': self.shares_outstanding
        }
        return symbol_dict
    
    def order_value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the required margin for a future order based on quantity.

        Parameters:
        - quantity (float): The quantity of the future order.

        Returns:
        - float: The calculated margin requirement for the future order.
        """
        return abs(quantity) * price
    
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
        super().__post_init__() 
        # Type checks
        if not isinstance(self.product_code, str):
            raise TypeError("'product_code' field must be of type str.")
        if not isinstance(self.product_name, str):
            raise TypeError("'product_name' field must be of type str.")
        if not isinstance(self.industry, Industry):
            raise TypeError("'industry' field must be of type Industry.")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError("'contract_size' field must be of type int or float.")
        if not isinstance(self.contract_units, ContractUnits):
            raise TypeError("'contract_units' field must be of type ContractUnits.")
        if not isinstance(self.tick_size, (int, float)):
            raise TypeError("'tick_size' field must be of type int or float.")
        if not isinstance(self.min_price_fluctuation, (int, float)):
            raise TypeError("'min_price_fluctuation' field must be of type int or float.")
        if not isinstance(self.continuous, bool):
            raise TypeError("'continuous' field must be of type boolean.")
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError(f"'lastTradeDateOrContractMonth' field must be a string.")

        # Constraint Checks
        if self.tick_size <= 0:
            raise ValueError(f"'tickSize' field must be greater than zero.")
    
        # Create contract object
        self.contract = self.to_contract()

    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = self.lastTradeDateOrContractMonth
        return data

    def to_dict(self):
        symbol_dict = super().to_dict() 
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

    def order_value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the required margin for a future order based on quantity.

        Parameters:
        - quantity (float): The quantity of the future order.

        Returns:
        - float: The calculated margin requirement for the future order.
        """
        return abs(quantity) * self.initial_margin

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
        super().__post_init__()  
        # Type checks
        if not isinstance(self.strike_price, (int, float)):
            raise TypeError("'strike_price' field must be of type int or float.")
        if not isinstance(self.expiration_date, str):
            raise TypeError("'expiration_date' field must be of type str.")
        if not isinstance(self.option_type,  Right):
            raise TypeError("'option_type' field must be of type Right.")
        if not isinstance(self.contract_size, (int, float)):
            raise TypeError("'contract_size' field must be of type int or float.")
        if not isinstance(self.underlying_name, str):
            raise TypeError("'underlying_name' must be of type str.")
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError(f"'lastTradeDateOrContractMonth' field must be a string.")
        
        # Constraint checks
        if self.strike_price <= 0:
            raise ValueError(f"'strike' field must be greater than zero.")
        
        # Create contract object
        self.contract = self.to_contract()
    
    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = self.lastTradeDateOrContractMonth
        data["right"] = self.option_type.value
        data["strike"] = self.strike_price
        return data
    
    def to_dict(self):
        symbol_dict = super().to_dict() 
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
    
    def order_value(self, quantity: float, price: Optional[float] = None) -> float:
        """
        Calculate the required margin for a future order based on quantity.

        Parameters:
        - quantity (float): The quantity of the future order.

        Returns:
        - float: The calculated margin requirement for the future order.
        """
        return abs(quantity) * price * self.quantity_multiplier

@dataclass
class Index(Symbol):
    name: str = None
    asset_class: AssetClass = None
    
    # Default
    fees: float = 0.0
    initial_margin: float = 0.0
    quantity_multiplier: int = 1
    price_multiplier: float = 1.0
    exchange: Venue= Venue.INDEX
    security_type: SecurityType = SecurityType.INDEX

    def __post_init__(self):
        super().__post_init__()  
        # Type checks
        if not isinstance(self.name, str):
            raise TypeError("'name' field must be of type str.")
        if not isinstance(self.asset_class, AssetClass):
            raise TypeError("'asset_class' field must be of type AssetClass.")
        
    def to_dict(self):
        symbol_dict = super().to_dict() 
        symbol_dict ["symbol_data"]= {
            'name': self.name,
            'currency': self.currency.value,
            'asset_class': self.asset_class.value,
            'venue': self.exchange.value
        }
        return symbol_dict
    
    def order_value(self, quantity: float, price: Optional[float] = None) -> float:
        pass
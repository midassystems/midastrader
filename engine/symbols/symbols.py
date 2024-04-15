from enum import Enum
from typing import Optional
from ibapi.contract import Contract
from dataclasses import dataclass, field

class Currency(Enum):
    USD = "USD"
    CAD = "CAD"

# Enum for Security Type
class SecType(Enum):
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    # ['STK', 'CMDTY','FUT','OPT','CASH','CRYPTO','FIGI','IND','CFD','FOP','BOND'] 

# Enum for Exchanges
class Exchange(Enum):
    SMART = "SMART"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    ISLAND = "ISLAND"
    CBOE = "CBOE"
    CME = "CME"
    COMEX = "COMEX"
    GLOBEX = "GLOBEX"
    CBOT = "CBOT"
    NYMEX = "NYMEX"

class Right(Enum):
    CALL = "C"
    PUT = "P"

@dataclass
class Symbol:
    ticker: str
    secType: SecType
    currency: Currency
    exchange: Exchange
    fees: float
    initialMargin: float
    quantity_multiplier: int = 1
    price_multiplier: float = 1
    data_ticker: Optional[str] = None
    contract: Contract = field(init=False)

    def __post_init__(self):
        # Type Validation
        if not isinstance(self.ticker, str):
            raise TypeError(f"ticker must be a string")
        if not isinstance(self.secType, SecType):
            raise TypeError(f"secType must be enum instance SecType")
        if not isinstance(self.currency, Currency):
            raise TypeError(f"currency must be enum instance Currency")
        if not isinstance(self.exchange, Exchange):
            raise TypeError(f"exchange must be enum instance Exchange")
        if not isinstance(self.fees,(float, int)):
            raise TypeError(f"fees must be int or float")
        if not isinstance(self.initialMargin, (float,int)):
            raise TypeError(f"initialMargin must be an int or float")
        if not isinstance(self.quantity_multiplier, (float,int)):
            raise TypeError(f"quantity_multiplier must be a int or float")
        if not isinstance(self.price_multiplier, (float, int)):
            raise TypeError(f"price_multiplier must be a int or float")
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
            "secType": self.secType.value,
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

@dataclass
class Equity(Symbol):
    def __init__(self, ticker: str, currency: Currency, exchange: Exchange, fees:float, data_ticker: str=None):
        super().__init__(ticker=ticker, data_ticker=data_ticker, secType=SecType.STOCK, currency=currency, exchange=exchange,quantity_multiplier=1,price_multiplier=1, initialMargin=0, fees=fees)

    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        return data

@dataclass
class Future(Symbol):
    lastTradeDateOrContractMonth: str = None
    tickSize: float = None
    # multiplier: int = None
    # price_multiplier:int = None
    # initialMargin : float = None

    def __init__(self, ticker: str, currency: Currency, exchange: Exchange,fees:float, lastTradeDateOrContractMonth: str, quantity_multiplier: int, price_multiplier: int, tickSize: float, initialMargin: float, data_ticker: str=None):
        self.lastTradeDateOrContractMonth = lastTradeDateOrContractMonth
        self.tickSize = tickSize
        # self.price_multiplier = price_multiplier
        # self.multiplier = multiplier
        # self.initialMargin = initialMargin
        super().__init__(ticker=ticker, data_ticker=data_ticker, secType=SecType.FUTURE, currency=currency, exchange=exchange, quantity_multiplier=quantity_multiplier, price_multiplier=price_multiplier, initialMargin=initialMargin, fees=fees)

    def __post_init__(self):
        # Type Validation
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError(f"lastTradeDateOrContractMonth must be a string")
        if not isinstance(self.tickSize, (float,int)):
            raise TypeError(f"tickSize must be a int or float")
        # if not isinstance(self.multiplier, (float,int)):
        #     raise TypeError(f"multiplier must be a int or float")
        # if not isinstance(self.price_multiplier, int):
        #     raise TypeError(f"price multiplier must be a int")
        # if not isinstance(self.initialMargin, (float,int)):
        #     raise TypeError(f"initialMargin must be an int or float")
        
        # Constraint Validation
        # if self.multiplier <= 0:
        #     raise ValueError(f"multiplier must be greater than 0")
        if self.tickSize <= 0:
            raise ValueError(f"tickSize must be greater than 0")
        # if self.initialMargin <= 0:
        #     raise ValueError(f"initialMargin must be greater than 0")

        super().__post_init__()

    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = self.lastTradeDateOrContractMonth
        # data['multiplier'] = self.multiplier
        return data
    
@dataclass
class Option(Symbol):
    lastTradeDateOrContractMonth: str = None 
    right: Right = None
    strike: float = None
    # multiplier: int = None

    def __init__(self, ticker: str, currency: Currency, exchange: Exchange,fees: float, lastTradeDateOrContractMonth: str, quantity_multiplier: int, price_multiplier: int, initialMargin: int, right: Right, strike: float, data_ticker: str=None):
        self.lastTradeDateOrContractMonth = lastTradeDateOrContractMonth
        self.right = right
        self.strike = strike
        # self.price_multiplier = price_multiplier
        # self.multiplier = multiplier
        super().__init__(ticker=ticker,data_ticker=data_ticker, secType=SecType.OPTION, currency=currency, exchange=exchange, quantity_multiplier=quantity_multiplier, price_multiplier=price_multiplier, initialMargin=initialMargin, fees=fees)

    def __post_init__(self):
        # Type Validation
        if not isinstance(self.lastTradeDateOrContractMonth, str):
            raise TypeError(f"lastTradeDateOrContractMonth must be a string")
        if not isinstance(self.right, Right):
            raise TypeError(f"right must be an instance of Right")
        if not isinstance(self.strike, (float,int)):
            raise TypeError(f"strike must be an int or float")
        # if not isinstance(self.multiplier, (float,int)):
        #     raise TypeError(f"multiplier must be a int or float")
        
        # Constraint Validation
        if self.strike <= 0:
            raise ValueError(f"strike must be greater than 0")
        # if self.multiplier <= 0:
        #     raise ValueError(f"multiplier must be greater than 0")

        super().__post_init__()


    def to_contract_data(self) -> dict:
        data = super().to_contract_data()
        data["lastTradeDateOrContractMonth"] = self.lastTradeDateOrContractMonth
        # data['multiplier'] = self.multiplier
        data["right"] = self.right.value  # Assuming Right is an Enum
        data["strike"] = self.strike
        return data
    

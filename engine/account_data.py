from typing import TypedDict, Union
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypedDict, Optional

class EquityDetails(TypedDict):
    timestamp : datetime
    equity_value : float
class AccountDetails(TypedDict):
    Timestamp: Optional[str]
    FullAvailableFunds : float # Available funds of whole portfolio with no discounts or intraday credits
    FullInitMarginReq: float # Initial Margin of whole portfolio with no discounts or intraday credits
    NetLiquidation: float # The basis for determining the price of the assets in your account
    UnrealizedPnL: float # The difference between the current market value of your open positions and the average cost, or Value - Average Cost
    # Live ONLY
    FullMaintMarginReq: Optional[float]
    ExcessLiquidity: Optional[float]
    Currency: Optional[str] # USD or CAD
    BuyingPower: Optional[float]
    FuturesPNL : Optional[float]
    TotalCashBalance: Optional[float] # Total Cash Balance including Future PNL

class ActiveOrder(TypedDict):
    permId: int
    clientId: int
    orderId: int
    parentId: int 
    account: str
    symbol: str
    secType: str
    exchange: str
    action: str 
    orderType: str
    totalQty: float
    cashQty: float
    lmtPrice: float
    auxPrice: float
    status: str  # Options : PendingSubmit, PendingCancel PreSubmitted, Submitted, Cancelled, Filled, Inactive 
    filled: str
    remaining: float
    avgFillPrice: float
    lastFillPrice: float 
    whyHeld: str 
    mktCapPrice: float

@dataclass
class Position:
    action: str  # BUY/SELL
    avg_cost: float
    quantity: int
    total_cost: Optional[float] 
    market_value: Optional[float]
    quantity_multiplier: int = None
    price_multiplier: int = None
    initial_margin: Optional[float] = None

    def __post_init__(self):
        # Type checks
        if not isinstance(self.action, str):
            raise TypeError(f"action must be of type str")
        if not isinstance(self.avg_cost, (int,float)):
            raise TypeError(f"avg_cost must be of type int or float")
        if not isinstance(self.quantity, (int,float)):
            raise TypeError(f"quantity must be of type int or float")
        if not isinstance(self.price_multiplier, (float, int)):
            raise TypeError(f"multiplier must be of type float or int")
        if not isinstance(self.quantity_multiplier, int):
            raise TypeError(f"multiplier must be of type int")
        if not isinstance(self.initial_margin, (int,float)):
            raise TypeError(f"initial_margin must be of type int or float") 
        if not isinstance(self.total_cost, (float, int)):
            raise TypeError(f"total_cost must be of type int or float")
        if not isinstance(self.market_value, (int, float)):
            raise TypeError(f"market_value must be of type int or float")
        

        # Constraint Validation
        if self.action not in ['BUY', 'SELL']:
            raise ValueError(f"action must be either 'BUY' or 'SELL'")
        if self.price_multiplier <= 0:
            raise ValueError(f"multiplier must be greater than zero")
        if self.quantity_multiplier <= 0:
            raise ValueError(f"multiplier must be greater than zero")
        if self.initial_margin < 0:
            raise ValueError(f"initial_margin must be non-negative.")
        
    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return (self.action == other.action and
                self.avg_cost == other.avg_cost and
                self.quantity == other.quantity and
                self.price_multiplier == other.price_multiplier and
                self.quantity_multiplier == other.quantity_multiplier and
                self.initial_margin == other.initial_margin and
                self.total_cost == other.total_cost)
    
    def to_dict(self):
        return {
            'action': self.action,
            'avg_cost': self.avg_cost,
            'quantity': self.quantity,
            'total_cost': self.total_cost,
            'market_value': self.market_value,
            'price_multiplier': self.price_multiplier,
            'quantity_multiplier': self.quantity_multiplier,
            'initial_margin': self.initial_margin
        }
    
@dataclass
class Trade:
    trade_id: int
    leg_id: int
    timestamp: Union[int,float]
    ticker: str
    quantity: Union[int,float]
    price: float
    cost: float
    action: str # BUY/SELL
    fees: float

    def __post_init__(self):
        # Type Validation
        if not isinstance(self.trade_id, int):
            raise TypeError(f"'trade_id' must be of type int")
        if not isinstance(self.leg_id, int):
            raise TypeError(f"'leg_id' must be of type int")
        if not isinstance(self.timestamp, (float,int)):
            raise TypeError(f"'timestamp' should be in UNIX format of type float or int, got {type(self.timestamp).__name__}")
        if not isinstance(self.ticker, str):
            raise TypeError(f"'ticker' must be of type str")
        if not isinstance(self.quantity, (float, int)):
            raise TypeError(f"'quantity' must be of type float or int")
        if not isinstance(self.price, (float, int)):
            raise TypeError(f"'price' must be of type float or int")
        if not isinstance(self.cost, (float, int)):
            raise TypeError(f"'cost' must be of type float or int")
        if not isinstance(self.action, str):
            raise TypeError(f"'action' must be of type str")
        if not isinstance(self.fees, (float, int)):
            raise TypeError(f"'fees' must be of type float or int")
        
        # Constraint Validation
        if self.action not in ['BUY', 'SELL', 'LONG', 'SHORT', 'COVER']:
            raise ValueError(f"'action' must be either 'BUY', 'SELL', 'LONG', 'SHORT', 'COVER'")
        if self.price <= 0:
            raise ValueError(f"'price' must be greater than zero")
        
        #TODO : Add validation for cost/quantity depending on the action

    # def __str__(self) -> str:
    #     return f"\nTrade: \n Timestamp: {self.timestamp}\n Trade ID:\n{self.trade_id}\n Leg ID:\n{self.leg_id}\n Ticker:\n{self.ticker}\n Quantity:\n{self.quantity}\n Price:\n{self.price}\n Cost:\n{self.cost}\n Action:\n{self.action}\n Fees:\n{self.fees}\n"
    
    def to_dict(self):
        return {
            "timestamp": datetime.fromtimestamp(self.timestamp, timezone.utc).isoformat(), # convert to isoformant form unix
            "trade_id": self.trade_id,
            "leg_id": self.leg_id,
            "ticker": self.ticker, 
            "quantity": self.quantity,
            "price": self.price, 
            "cost": self.cost,
            "action": self.action, 
            "fees": self.fees
        }


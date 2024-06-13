import numpy as np
from dataclasses import dataclass
from typing import Optional, TypedDict, Dict

class EquityDetails(TypedDict):
    timestamp: np.uint64
    equity_value: float

class AccountDetails(TypedDict):
    timestamp: np.uint64
    full_available_funds: float
    full_init_margin_req: float 
    net_liquidation: float 
    unrealized_pnl: float 
    full_maint_margin_req: Optional[float] 
    excess_liquidity: Optional[float]
    currency: Optional[str] 
    buying_power: Optional[float]
    futures_pnl: Optional[float]
    total_cash_balance: Optional[float] 
    
@dataclass
class Account:
    timestamp: np.uint64
    full_available_funds: float                 # Available funds of whole portfolio with no discounts or intraday credits
    full_init_margin_req: float                 # Initial Margin of whole portfolio with no discounts or intraday credits
    net_liquidation: float                      # The basis for determining the price of the assets in your account
    unrealized_pnl: float                       # The difference between the current market value of your open positions and the average cost, or Value - Average Cost
    full_maint_margin_req: Optional[float] = 0
    excess_liquidity: Optional[float] = 0
    currency: Optional[str]  = ""               # USD or CAD
    buying_power: Optional[float] = 0.0
    futures_pnl: Optional[float] = 0.0
    total_cash_balance: Optional[float] = 0.0   # Total Cash Balance including Future PNL

    def __post_init__(self):
        # Type Check
        if not isinstance(self.timestamp, (np.uint64, type(None))):
            raise TypeError("'timestamp' field must be of type int or np.uint64.")
        if not isinstance(self.full_available_funds, (int, float)):
            raise TypeError("'full_available_funds' field must be of type int or float.")
        if not isinstance(self.full_init_margin_req, (int, float)):
            raise TypeError("'full_init_margin_req' must be of type int or float.")
        if not isinstance(self.net_liquidation, (int, float)):
            raise TypeError("'net_liquidation' field must be of type int or float.")
        if not isinstance(self.unrealized_pnl, (int, float)):
            raise TypeError("'unrealized_pnl' field must be of type int or float.")
        if not isinstance(self.full_maint_margin_req, (int, float)):
            raise TypeError("'full_maint_margin_req' field must be of type int or float.")
        if not isinstance(self.excess_liquidity, (int, float)):
            raise TypeError("'excess_liquidity' field must be of type int or float.")
        if not isinstance(self.buying_power, (int, float)):
            raise TypeError("'buying_power' field must be of type int or float.")
        if not isinstance(self.futures_pnl, (int, float)):
            raise TypeError("'futures_pnl' field must be of type int or float.")
        if not isinstance(self.currency, str):
            raise TypeError("'currency' field must be of type str.")
        if not isinstance(self.total_cash_balance, (int, float)):
            raise TypeError("'total_cash_balance' field must be of type int or float.")
        
    @property
    def capital(self):
        return self.full_available_funds
    
    @staticmethod
    def get_ibapi_keys() -> staticmethod:
        ibapi_keys = "Timestamp,FullAvailableFunds,FullInitMarginReq,NetLiquidation,UnrealizedPnL,FullMaintMarginReq,ExcessLiquidity,Currency,BuyingPower,FuturesPNL,TotalCashBalance"
        return ibapi_keys
    
    @staticmethod
    def get_account_key_mapping() -> Dict[str, str]:
        return {
            "Timestamp": "timestamp",
            "FullAvailableFunds": "full_available_funds",
            "FullInitMarginReq": "full_init_margin_req",
            "NetLiquidation": "net_liquidation",
            "UnrealizedPnL": "unrealized_pnl",
            "FullMaintMarginReq": "full_maint_margin_req",
            "ExcessLiquidity": "excess_liquidity",
            "Currency": "currency",
            "BuyingPower": "buying_power",
            "FuturesPNL": "futures_pnl",
            "TotalCashBalance": "total_cash_balance"
        }

    def update_from_broker_data(self, broker_key: str, value: any):
        mapping = self.get_account_key_mapping()
        if broker_key in mapping:
            setattr(self, mapping[broker_key], value)
    
    def equity_value(self) -> EquityDetails:
        """
        Returns EquityDetails dictionary containing the full equity value and the timestamp.

        Returns:
         - EquityDetails (dict): Representing the equity value at a point in time.
        """
        return EquityDetails(timestamp=self.timestamp, equity_value=round(self.net_liquidation, 2))

    def check_margin_call(self) -> bool:
        """
        Checks if a margin call is triggered based on available funds and initial margin requirements.

        Returns:
        - bool: True if a margin call is triggered, False otherwise.
        """
        if self.full_available_funds < self.full_init_margin_req:
            
            return True
        return False

    def to_dict(self) -> AccountDetails:
        """ Returns AccountDetails dictionary of Acount data. """
        return AccountDetails(
            timestamp=self.timestamp,
            full_available_funds=self.full_available_funds,
            full_init_margin_req=self.full_init_margin_req,
            net_liquidation=self.net_liquidation,
            unrealized_pnl=self.unrealized_pnl,
            full_maint_margin_req=self.full_maint_margin_req,
            excess_liquidity=self.excess_liquidity,
            currency=self.currency,
            buying_power=self.buying_power,
            futures_pnl=self.futures_pnl,
            total_cash_balance=self.total_cash_balance
        )

    def pretty_print(self) -> str:
        """ Returns str of Account data for outputting. """
        string = ""
        string += f"  Timestamp: {self.timestamp}\n"
        string += f"  FullAvailableFunds: {self.full_available_funds}\n"
        string += f"  FullInitMarginReq: {self.full_init_margin_req}\n"
        string += f"  NetLiquidation: {self.net_liquidation}\n"
        string += f"  UnrealizedPnL: {self.unrealized_pnl}\n"
        string += f"  FullMaintMarginReq: {self.full_maint_margin_req}\n"
        string += f"  ExcessLiquidity: {self.excess_liquidity}\n"
        string += f"  Currency: {self.currency}\n"
        string += f"  BuyingPower: {self.buying_power}\n"
        string += f"  FuturesPNL: {self.futures_pnl}\n"
        string += f"  TotalCashBalance: {self.total_cash_balance}\n"
        return string


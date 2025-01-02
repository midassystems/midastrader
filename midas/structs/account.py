from dataclasses import dataclass
from typing import Optional, TypedDict, Dict


class EquityDetails(TypedDict):
    """
    A TypedDict representing equity details for the account.

    Attributes:
        timestamp (int): The timestamp of the equity snapshot.
        equity_value (float): The rounded net liquidation value representing equity.
    """

    timestamp: int
    equity_value: float


@dataclass
class Account:
    """
    Represents an account with margin, equity, and cash balance details.

    Attributes:
        timestamp (int): The timestamp of the account snapshot.
        full_available_funds (float): Total available funds without discounts or intraday credits.
        full_init_margin_req (float): Initial margin requirement without discounts.
        net_liquidation (float): The net liquidation value (assets' current price).
        unrealized_pnl (float): Unrealized profit and loss (PnL) for open positions.
        full_maint_margin_req (Optional[float]): Maintenance margin requirement.
        excess_liquidity (Optional[float]): Excess liquidity beyond margin requirements.
        currency (Optional[str]): The account currency (e.g., "USD", "CAD").
        buying_power (Optional[float]): The buying power available for trading.
        futures_pnl (Optional[float]): Profit or loss from futures positions.
        total_cash_balance (Optional[float]): Total cash balance including futures PnL.
    """

    timestamp: int
    full_available_funds: float
    full_init_margin_req: float
    net_liquidation: float
    unrealized_pnl: float
    full_maint_margin_req: Optional[float] = 0
    excess_liquidity: Optional[float] = 0
    currency: Optional[str] = ""
    buying_power: Optional[float] = 0.0
    futures_pnl: Optional[float] = 0.0
    total_cash_balance: Optional[float] = 0.0

    def __post_init__(self):
        """
        Validates the types of input fields after initialization.

        Raises:
            TypeError: If any attribute has an incorrect type.
        """
        # Type Check
        if not isinstance(self.timestamp, (int, type(None))):
            raise TypeError("'timestamp' must be int or np.uint64.")
        if not isinstance(self.full_available_funds, (int, float)):
            raise TypeError("'full_available_funds' must be int or float.")
        if not isinstance(self.full_init_margin_req, (int, float)):
            raise TypeError("'full_init_margin_req' must be int or float.")
        if not isinstance(self.net_liquidation, (int, float)):
            raise TypeError("'net_liquidation' must be int or float.")
        if not isinstance(self.unrealized_pnl, (int, float)):
            raise TypeError("'unrealized_pnl' must be int or float.")
        if not isinstance(self.full_maint_margin_req, (int, float)):
            raise TypeError("'full_maint_margin_req' must be int or float.")
        if not isinstance(self.excess_liquidity, (int, float)):
            raise TypeError("'excess_liquidity' must be int or float.")
        if not isinstance(self.buying_power, (int, float)):
            raise TypeError("'buying_power' must be int or float.")
        if not isinstance(self.futures_pnl, (int, float)):
            raise TypeError("'futures_pnl' must be int or float.")
        if not isinstance(self.currency, str):
            raise TypeError("'currency' must be str.")
        if not isinstance(self.total_cash_balance, (int, float)):
            raise TypeError("'total_cash_balance' must be int or float.")

    @property
    def capital(self) -> float:
        """
        Returns the full available funds as the account's capital.

        Returns:
            float: Full available funds.
        """
        return self.full_available_funds

    @staticmethod
    def get_ibapi_keys() -> str:
        """
        Provides a comma-separated string of Interactive Brokers (IBAPI) account keys.

        Returns:
            str: A string of IBAPI account keys.
        """
        return "Timestamp,FullAvailableFunds,FullInitMarginReq,NetLiquidation,UnrealizedPnL,FullMaintMarginReq,ExcessLiquidity,Currency,BuyingPower,FuturesPNL,TotalCashBalance"

    @staticmethod
    def get_account_key_mapping() -> Dict[str, str]:
        """
        Maps IBAPI account keys to Account class attributes.

        Returns:
            Dict[str, str]: A dictionary mapping broker keys to Account attribute names.
        """
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
            "TotalCashBalance": "total_cash_balance",
        }

    def update_from_broker_data(self, broker_key: str, value: any):
        """
        Updates account attributes based on data received from the broker.

        Args:
            broker_key (str): The key provided by the broker.
            value (any): The value to update the attribute with.
        """
        mapping = self.get_account_key_mapping()
        if broker_key in mapping:
            setattr(self, mapping[broker_key], value)

    def equity_value(self) -> EquityDetails:
        """
        Returns equity details, including the timestamp and net liquidation value.

        Returns:
            EquityDetails: A dictionary containing `timestamp` and `equity_value`.
        """
        return EquityDetails(
            timestamp=self.timestamp,
            equity_value=round(self.net_liquidation, 2),
        )

    def check_margin_call(self) -> bool:
        """
        Checks if a margin call is triggered.

        A margin call is triggered if the full available funds fall below
        the initial margin requirement.

        Returns:
            bool: True if a margin call is triggered, False otherwise.
        """
        return self.full_available_funds < self.full_init_margin_req

    def to_dict(self, prefix: str = "") -> dict:
        """
        Converts the account object into a dictionary with an optional prefix.

        Args:
            prefix (str): An optional string prefix for all dictionary keys.

        Returns:
            dict: A dictionary representation of the account.
        """
        return {
            f"{prefix}timestamp": self.timestamp,
            f"{prefix}full_available_funds": self.full_available_funds,
            f"{prefix}full_init_margin_req": self.full_init_margin_req,
            f"{prefix}net_liquidation": self.net_liquidation,
            f"{prefix}unrealized_pnl": self.unrealized_pnl,
            f"{prefix}full_maint_margin_req": self.full_maint_margin_req,
            f"{prefix}excess_liquidity": self.excess_liquidity,
            f"{prefix}buying_power": self.buying_power,
            f"{prefix}futures_pnl": self.futures_pnl,
            f"{prefix}total_cash_balance": self.total_cash_balance,
            "currency": self.currency,
        }

    def pretty_print(self, indent: str = "") -> str:
        """
        Generates a human-readable string representation of the account.

        Args:
            indent (str): Optional indentation string for formatting.

        Returns:
            str: A formatted string containing account details.
        """
        return (
            f"{indent}Timestamp: {self.timestamp}\n"
            f"{indent}FullAvailableFunds: {self.full_available_funds}\n"
            f"{indent}FullInitMarginReq: {self.full_init_margin_req}\n"
            f"{indent}NetLiquidation: {self.net_liquidation}\n"
            f"{indent}UnrealizedPnL: {self.unrealized_pnl}\n"
            f"{indent}FullMaintMarginReq: {self.full_maint_margin_req}\n"
            f"{indent}ExcessLiquidity: {self.excess_liquidity}\n"
            f"{indent}Currency: {self.currency}\n"
            f"{indent}BuyingPower: {self.buying_power}\n"
            f"{indent}FuturesPNL: {self.futures_pnl}\n"
            f"{indent}TotalCashBalance: {self.total_cash_balance}\n"
        )

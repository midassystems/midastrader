from dataclasses import dataclass
from typing import Union


@dataclass
class Trade:
    timestamp: int
    trade_id: int
    leg_id: int
    instrument: int
    quantity: Union[int, float]
    avg_price: float
    trade_value: float
    trade_cost: float
    action: str  # BUY/SELL
    fees: float

    def __post_init__(self):
        # Type Check
        if not isinstance(self.timestamp, int):
            raise TypeError("'timestamp' field must be of type int.")
        if not isinstance(self.trade_id, int):
            raise TypeError("'trade_id' field must be of type int.")
        if not isinstance(self.leg_id, int):
            raise TypeError("'leg_id' field must be of type int.")
        if not isinstance(self.instrument, int):
            raise TypeError("'instrument' field must be of type int.")
        if not isinstance(self.quantity, (float, int)):
            raise TypeError("'quantity' field must be of type float or int.")
        if not isinstance(self.avg_price, (float, int)):
            raise TypeError("'avg_price' field must be of type float or int.")
        if not isinstance(self.trade_value, (float, int)):
            raise TypeError(
                "'trade_value' field must be of type float or int."
            )
        if not isinstance(self.trade_cost, (float, int)):
            raise TypeError("'trade_cost' field must be of type float or int.")
        if not isinstance(self.action, str):
            raise TypeError("'action' field must be of type str.")
        if not isinstance(self.fees, (float, int)):
            raise TypeError("'fees' field must be of type float or int.")

        # Value Constraint
        if self.action not in ["BUY", "SELL", "LONG", "SHORT", "COVER"]:
            raise ValueError(
                "'action' field must be in ['BUY', 'SELL', 'LONG', 'SHORT', 'COVER']."
            )
        if self.avg_price <= 0:
            raise ValueError("'avg_price' field must be greater than zero.")

    def to_dict(self):
        return {
            "timestamp": int(self.timestamp),
            "trade_id": self.trade_id,
            "leg_id": self.leg_id,
            "ticker": self.instrument,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "trade_value": self.trade_value,
            "trade_cost": self.trade_cost,
            "action": self.action,
            "fees": self.fees,
        }

    def pretty_print(self, indent: str = "") -> str:
        return (
            f"{indent}Timestamp: {self.timestamp}\n"
            f"{indent}Trade ID: {self.trade_id}\n"
            f"{indent}Leg ID: {self.leg_id}\n"
            f"{indent}Instrument: {self.instrument}\n"
            f"{indent}Quantity: {self.quantity}\n"
            f"{indent}Avg Price: {self.avg_price}\n"
            f"{indent}Notional Value: {self.trade_value}\n"
            f"{indent}Trade Cost: {self.trade_cost}\n"
            f"{indent}Action: {self.action}\n"
            f"{indent}Fees: {self.fees}\n"
        )

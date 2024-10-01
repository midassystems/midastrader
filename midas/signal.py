from dataclasses import dataclass
from typing import Union, Optional
from midas.orders import (
    OrderType,
    Action,
    BaseOrder,
    MarketOrder,
    StopLoss,
    LimitOrder,
)


@dataclass
class TradeInstruction:
    instrument: int
    order_type: OrderType
    action: Action
    trade_id: int
    leg_id: int
    weight: float
    quantity: Union[int, float]
    limit_price: Optional[float] = None
    aux_price: Optional[float] = None

    def __post_init__(self):
        # Type Check
        if not isinstance(self.instrument, int):
            raise TypeError("'instrument' field must be of type int.")
        if not isinstance(self.order_type, OrderType):
            raise TypeError(
                "'order_type' field must be of type OrderType enum."
            )
        if not isinstance(self.action, Action):
            raise TypeError("'action' field must be of type Action enum.")
        if not isinstance(self.trade_id, int):
            raise TypeError("'trade_id' field must of type int.")
        if not isinstance(self.leg_id, int):
            raise TypeError("'leg_id' field must be of type int.")
        if not isinstance(self.quantity, (int, float)):
            raise TypeError("'quantity' field must be of type int or float.")
        if self.order_type == OrderType.LIMIT and not isinstance(
            self.limit_price, (int, float)
        ):
            raise TypeError(
                "'limit_price' field must be int or float for OrderType.LIMIT."
            )
        if self.order_type == OrderType.STOPLOSS and not isinstance(
            self.aux_price, (int, float)
        ):
            raise TypeError(
                "'aux_price' field must be int or float for OrderType.STOPLOSS."
            )

        # Value Constraint
        if self.trade_id <= 0:
            raise ValueError("'trade_id' field must be greater than zero.")
        if self.leg_id <= 0:
            raise ValueError("'leg_id' field must must be greater than zero.")
        if self.limit_price and self.limit_price <= 0:
            raise ValueError(
                "'limit_price' field must must be greater than zero."
            )
        if self.aux_price and self.aux_price <= 0:
            raise ValueError(
                "'aux_price' field must must be greater than zero."
            )

    def to_dict(self):
        return {
            "ticker": self.instrument,
            "order_type": self.order_type.value,
            "action": self.action.value,
            "trade_id": self.trade_id,
            "leg_id": self.leg_id,
            "weight": round(self.weight, 4),
            "quantity": self.quantity,
            "limit_price": (self.limit_price if self.limit_price else ""),
            "aux_price": self.aux_price if self.aux_price else "",
        }

    def to_order(self) -> BaseOrder:
        if self.order_type == OrderType.MARKET:
            return MarketOrder(action=self.action, quantity=self.quantity)
        elif self.order_type == OrderType.LIMIT:
            return LimitOrder(
                action=self.action,
                quantity=self.quantity,
                limit_price=self.limit_price,
            )
        elif self.order_type == OrderType.STOPLOSS:
            return StopLoss(
                action=self.action,
                quantity=self.quantity,
                aux_price=self.aux_price,
            )

    def __str__(self) -> str:
        return (
            f"Instrument: {self.instrument}, "
            f"Order Type: {self.order_type.name}, "
            f"Action: {self.action.name}, "
            f"Trade ID: {self.trade_id}, "
            f"Leg ID: {self.leg_id}, "
            f"Weight: {self.weight}, "
            f"Quantity: {self.quantity}, "
            f"Limit Price: {self.limit_price if self.limit_price else ''}, "
            f"Aux Price:  {self.aux_price if self.aux_price else ''}"
        )

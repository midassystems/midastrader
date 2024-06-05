# shared/signal.py
from typing import List, Union, Optional
from dataclasses import dataclass

from midas.shared.orders import OrderType, Action, BaseOrder , MarketOrder, StopLoss, LimitOrder

@dataclass
class TradeInstruction:
    ticker: str
    order_type: OrderType
    action: Action
    trade_id: int
    leg_id: int
    weight: float
    quantity: Union[int, float]
    limit_price: Optional[float]=None
    aux_price: Optional[float]=None

    def __post_init__(self):
        self._data_validation()

    def _data_validation(self):
        if not self.ticker or not isinstance(self.ticker, str):
            raise ValueError("'ticker' must be a non-empty string.")
        
        if not isinstance(self.order_type, OrderType):
            raise ValueError("'order_type' must be of type OrderType enum.")
        
        if not isinstance(self.action, Action):
            raise ValueError("'action' must be of type Action enum.")
        
        if not isinstance(self.trade_id, int) or self.trade_id <= 0:
            raise ValueError("'trade_id' must be a non-negative integer.")
        
        if not isinstance(self.leg_id, int) or self.leg_id <= 0:
            raise ValueError("'leg_id' must be a non-negative integer.")
    
        if not isinstance(self.quantity, (int,float)):
            raise ValueError("'quantity' must be an int or float.")
        
        if self.order_type == OrderType.LIMIT and self.limit_price == None:
            raise ValueError("'limit_price' cannot be None for OrderType.LIMIT.")
        
        if self.order_type == OrderType.STOPLOSS and self.aux_price == None:
            raise ValueError("'aux_price' cannot be None for OrderType.STOPLOSS.")
            

    def to_dict(self):
        return {
            "ticker": self.ticker,
            "order_type": self.order_type.value,
            "action": self.action.value,
            "trade_id": self.trade_id,
            "leg_id": self.leg_id,
            "weight": round(self.weight,4),
            "quantity":self.quantity
        }
    
    def to_order(self) -> BaseOrder:
        if self.order_type == OrderType.MARKET:
            return MarketOrder(action=self.action, quantity=self.quantity)
        elif self.order_type == OrderType.LIMIT:    
            return LimitOrder(action=self.action, quantity=self.quantity, limit_price=self.limit_price)
        elif self.order_type == OrderType.STOPLOSS:
            return StopLoss(action=self.action, quantity=self.quantity,aux_price=self.aux_price)

    def __str__(self) -> str:
        return (
            f"Ticker: {self.ticker}, "
            f"Order Type: {self.order_type.name}, "
            f"Action: {self.action.name}, "
            f"Trade ID: {self.trade_id}, "
            f"Leg ID: {self.leg_id}, "
            f"Weight: {self.weight}, "
            f"Quantity: {self.quantity}"
        )
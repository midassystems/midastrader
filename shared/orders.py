# shared/orders.py
from enum import Enum 
from typing  import  Any
from ibapi.order import Order


class Action(Enum):
    """ Long and short are treated as entry actions and short/cover are treated as exit actions. """
    LONG = 'LONG'  # BUY
    COVER = 'COVER' # BUY
    SHORT = 'SHORT' # SELL
    SELL = 'SELL'  # SELL

    def to_broker_standard(self):
        """Converts the enum to the standard BUY or SELL action for the broker."""
        if self in [Action.LONG, Action.COVER]:
            return 'BUY'
        elif self in [Action.SHORT, Action.SELL]:
            return 'SELL'
        else:
            raise ValueError(f"Invalid action: {self}")
        
class OrderType(Enum):
    """ Interactive Brokers Specific """
    MARKET = "MKT"
    LIMIT = "LMT"
    STOPLOSS = "STP"

class BaseOrder:
    """ 
    Base class for order creation. Should not be used directly, access through a subclass.
    """
    def __init__(self, action: Action, quantity: float, orderType: OrderType) -> None:
        # Type Check
        if not isinstance(action, Action):
            raise TypeError("'action' must be type Action enum.")
        if not isinstance(quantity,(float, int)):
            raise TypeError("'quantity' must be type float or int.")
        if not isinstance(orderType,OrderType):
            raise TypeError("'orderType' must be type OrderType enum.")
        
        broker_action = action.to_broker_standard()
        
        # Constraints
        if broker_action  not in ['BUY', 'SELL']:
            raise ValueError("action must be either 'BUY' or 'SELL'")
        if quantity == 0:
            raise ValueError("'quantity' must not be zero.")
        
        self.order = Order()
        self.order.action = broker_action 
        self.order.orderType = orderType.value
        self.order.totalQuantity = abs(quantity)
    
    @property
    def quantity(self):
        return self.order.totalQuantity if self.order.action == 'BUY' else -self.order.totalQuantity

class MarketOrder(BaseOrder):
    def __init__(self, action: Action, quantity: float):
        super().__init__(action, quantity, OrderType.MARKET)

class LimitOrder(BaseOrder):
    def __init__(self, action: Action, quantity: float, limit_price: float):
        if not isinstance(limit_price, (float,int)):
            raise TypeError("'limit_price' must be of type float or int.")
        if limit_price <= 0:
            raise ValueError("'limit_price' must be greater than zero.")
        
        super().__init__(action, quantity, OrderType.LIMIT)
        self.order.lmtPrice = limit_price
        
class StopLoss(BaseOrder):
    def __init__(self, action: Action, quantity: float, aux_price: float) -> None:
        if not isinstance(aux_price,(float, int)):
            raise TypeError("'aux_price' must be of type float or int.")
        if aux_price <= 0:
            raise ValueError("'aux_price' must be greater than zero.")
        
        super().__init__(action, quantity, OrderType.STOPLOSS)
        self.order.auxPrice = aux_price

from abc import ABC
from enum import Enum
from ibapi.order import Order


class Action(Enum):
    """
    Enum representing the possible trade actions.
    LONG and SHORT actions are treated as entry actions,
    while COVER and SELL are treated as exit actions.

    Attributes:
        LONG (str): Represents a BUY action for entering a long position.
        COVER (str): Represents a BUY action for covering a short position.
        SHORT (str): Represents a SELL action for entering a short position.
        SELL (str): Represents a SELL action for exiting a long position.
    """

    LONG = "LONG"
    COVER = "COVER"
    SHORT = "SHORT"
    SELL = "SELL"

    def to_broker_standard(self):
        """
        Converts the Action enum into the standard 'BUY' or 'SELL' actions
        expected by the broker.

        Returns:
            str: 'BUY' for LONG/COVER actions, 'SELL' for SHORT/SELL actions.

        Raises:
            ValueError: If the action is invalid or unrecognized.
        """
        if self in [Action.LONG, Action.COVER]:
            return "BUY"
        elif self in [Action.SHORT, Action.SELL]:
            return "SELL"
        else:
            raise ValueError(f"Invalid action: {self}")


class OrderType(Enum):
    """
    Enum representing order types specific to Interactive Brokers.

    Attributes:
        MARKET (str): Market order, executed at the current market price.
        LIMIT (str): Limit order, executed at a specified price or better.
        STOPLOSS (str): Stop-loss order, triggered when a specified price is reached.
    """

    MARKET = "MKT"
    LIMIT = "LMT"
    STOPLOSS = "STP"


class BaseOrder(ABC):
    """
    Abstract base class for creating order objects.
    This class provides a foundational structure for various order types.

    Args:
        action (Action): The action for the order (e.g., LONG, SELL).
        quantity (float|int): The quantity of the financial instrument to trade.
        order_type (OrderType): The type of order (e.g., MARKET, LIMIT, STOPLOSS).

    Attributes:
        order (ibapi.order.Order): The Interactive Brokers Order object,
            populated with the specified parameters.

    Raises:
        TypeError: If any of the inputs have incorrect types.
        ValueError: If `quantity` is zero or invalid.
    """

    def __init__(
        self,
        action: Action,
        quantity: float,
        order_type: OrderType,
    ) -> None:
        # Type Check
        if not isinstance(action, Action):
            raise TypeError("'action' field must be type Action enum.")
        if not isinstance(quantity, (float, int)):
            raise TypeError("'quantity' field must be type float or int.")
        if not isinstance(order_type, OrderType):
            raise TypeError("'order_type' field must be type OrderType enum.")

        # Convert to BUY/SELL
        broker_action = action.to_broker_standard()

        # Value Constraints
        if quantity == 0:
            raise ValueError("'quantity' field must not be zero.")

        # Create interactive brokers Order object
        self.order = Order()
        self.order.action = broker_action
        self.order.orderType = order_type.value
        self.order.totalQuantity = abs(quantity)

    @property
    def quantity(self):
        """
        Returns the signed quantity of the order.

        Returns:
            float: Positive quantity for 'BUY', negative for 'SELL'.
        """
        return (
            self.order.totalQuantity
            if self.order.action == "BUY"
            else -self.order.totalQuantity
        )


class MarketOrder(BaseOrder):
    """
    Represents a market order, executed immediately at the current market price.

    Args:
        action (Action): The action of the order (e.g., LONG, SELL).
        quantity (float): The amount of the asset to be traded.

    Example:
        buy_order = MarketOrder(action=Action.LONG, quantity=100)
    """

    def __init__(self, action: Action, quantity: float):
        super().__init__(action, quantity, OrderType.MARKET)


class LimitOrder(BaseOrder):
    """
    Represents a limit order, executed at a specified price or better.

    Args:
        action (Action): The action of the order (e.g., SHORT, SELL).
        quantity (float): The amount of the asset to be traded.
        limit_price (float|int): The price limit for the trade.

    Raises:
        TypeError: If `limit_price` is not a float or int.
        ValueError: If `limit_price` is not greater than zero.

    Example:
        sell_order = LimitOrder(action=Action.SELL, quantity=50, limit_price=150.25)
    """

    def __init__(self, action: Action, quantity: float, limit_price: float):
        if not isinstance(limit_price, (float, int)):
            raise TypeError(
                "'limit_price' field must be of type float or int."
            )

        if limit_price <= 0:
            raise ValueError("'limit_price' field must be greater than zero.")

        super().__init__(action, quantity, OrderType.LIMIT)
        self.order.lmtPrice = limit_price


class StopLoss(BaseOrder):
    """
    Represents a stop-loss order, triggered when a specified price point is reached.

    Args:
        action (Action): The action of the order (e.g., SHORT, COVER).
        quantity (float): The amount of the asset to be traded.
        aux_price (float|int): The stop price that triggers the order.

    Raises:
        TypeError: If `aux_price` is not a float or int.
        ValueError: If `aux_price` is not greater than zero.

    Example:
        stop_loss_order = StopLoss(action=Action.COVER, quantity=100, aux_price=300.50)
    """

    def __init__(
        self, action: Action, quantity: float, aux_price: float
    ) -> None:
        if not isinstance(aux_price, (float, int)):
            raise TypeError("'aux_price' field must be of type float or int.")
        if aux_price <= 0:
            raise ValueError("'aux_price' field must be greater than zero.")

        super().__init__(action, quantity, OrderType.STOPLOSS)
        self.order.auxPrice = aux_price

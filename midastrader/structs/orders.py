from abc import ABC
from decimal import Decimal
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
    DEFAULT = "DEFAULT"

    @classmethod
    def from_string(cls, action_str: str) -> "Action":
        """Convert a string to a Action enum, ensuring case-insensitivity."""
        try:
            if action_str == "BUY":
                return Action.LONG
            else:
                return cls[action_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid action: {action_str}.")

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
    DEFAULT = "DEFAULT"

    @classmethod
    def from_string(cls, order_str: str) -> "OrderType":
        """Convert a string to a OrderType enum, ensuring case-insensitivity."""
        try:
            return cls[order_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid OrderType:  {order_str}.")


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
        instrument_id: int,
        signal_id: int,
        action: Action,
        quantity: float,
        order_type: OrderType,
    ) -> None:

        self.instrument_id: int = instrument_id
        self.signal_id: int = signal_id
        self.action: Action = action
        self.quantity: float = quantity
        self.order_type: OrderType = order_type

        # Type Check
        if not isinstance(self.instrument_id, int):
            raise TypeError("'instrument_id' field must be type int.")
        if not isinstance(self.signal_id, int):
            raise TypeError("'signal_id' field must be type int.")
        if not isinstance(self.action, Action):
            raise TypeError("'action' field must be type Action enum.")
        if not isinstance(self.quantity, (float, int)):
            raise TypeError("'quantity' field must be type float or int.")
        if not isinstance(self.order_type, OrderType):
            raise TypeError("'order_type' field must be type OrderType enum.")

        # Value Constraints
        if self.quantity == 0:
            raise ValueError("'quantity' field must not be zero.")

    def ib_order(self) -> Order:

        # Convert to BUY/SELL
        broker_action = self.action.to_broker_standard()

        # Create interactive brokers Order object
        order = Order()
        order.action = broker_action
        order.orderType = self.order_type.value
        order.totalQuantity = Decimal(abs(self.quantity))

        return order


class MarketOrder(BaseOrder):
    """
    Represents a market order, executed immediately at the current market price.

    Args:
        action (Action): The action of the order (e.g., LONG, SELL).
        quantity (float): The amount of the asset to be traded.

    Example:
        buy_order = MarketOrder(action=Action.LONG, quantity=100)
    """

    def __init__(
        self,
        instrument_id: int,
        signal_id: int,
        action: Action,
        quantity: float,
    ) -> None:
        super().__init__(
            instrument_id,
            signal_id,
            action,
            quantity,
            OrderType.MARKET,
        )

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the MarketOrder.

        Returns:
            str: A formatted string with the signal's details.
        """
        return (
            f"Instrument: {self.instrument_id}, "
            f"Order Type: {self.order_type.name}, "
            f"Action: {self.action.name}, "
            f"Signal ID: {self.signal_id}, "
            f"Quantity: {self.quantity}, "
        )


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

    def __init__(
        self,
        instrument_id: int,
        signal_id: int,
        action: Action,
        quantity: float,
        limit_price: float,
    ) -> None:
        super().__init__(
            instrument_id,
            signal_id,
            action,
            quantity,
            OrderType.LIMIT,
        )

        self.limit_price: float = limit_price

        if not isinstance(self.limit_price, (float, int)):
            raise TypeError(
                "'limit_price' field must be of type float or int."
            )

        if self.limit_price <= 0:
            raise ValueError("'limit_price' field must be greater than zero.")

    def ib_order(self) -> Order:
        order = super().ib_order()
        order.lmtPrice = self.limit_price
        return order

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the LimitOrder.

        Returns:
            str: A formatted string with the signal's details.
        """
        return (
            f"Instrument: {self.instrument_id}, "
            f"Order Type: {self.order_type.name}, "
            f"Action: {self.action.name}, "
            f"Signal ID: {self.signal_id}, "
            f"Quantity: {self.quantity}, "
            f"Limit Price: {self.limit_price if self.limit_price else ''}, "
        )


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
        self,
        instrument_id: int,
        signal_id: int,
        action: Action,
        quantity: float,
        aux_price: float,
    ) -> None:
        super().__init__(
            instrument_id,
            signal_id,
            action,
            quantity,
            OrderType.STOPLOSS,
        )

        self.aux_price: float = aux_price

        if not isinstance(self.aux_price, (float, int)):
            raise TypeError("'aux_price' field must be of type float or int.")
        if self.aux_price <= 0:
            raise ValueError("'aux_price' field must be greater than zero.")

    def ib_order(self) -> Order:
        order = super().ib_order()
        order.auxPrice = self.aux_price
        return order

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the StopLoss.

        Returns:
            str: A formatted string with the signal's details.
        """
        return (
            f"Instrument: {self.instrument_id}, "
            f"Order Type: {self.order_type.name}, "
            f"Action: {self.action.name}, "
            f"Signal ID: {self.signal_id}, "
            f"Quantity: {self.quantity}, "
            f"Aux Price:  {self.aux_price if self.aux_price else ''}"
        )

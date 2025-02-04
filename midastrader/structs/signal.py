import mbn
from dataclasses import dataclass
from typing import Optional

from midastrader.structs.constants import PRICE_FACTOR
from midastrader.structs.orders import (
    OrderType,
    Action,
    BaseOrder,
    MarketOrder,
    StopLoss,
    LimitOrder,
)


@dataclass
class SignalInstruction:
    """
    Represents a trading signal that specifies an instrument, order type, and
    additional parameters needed to construct an order.

    Attributes:
        instrument (int): The identifier for the traded instrument (e.g., ticker ID).
        order_type (OrderType): The type of order, defined in the OrderType enum.
        action (Action): The action to perform, e.g., BUY or SELL, defined in the Action enum.
        trade_id (int): A unique identifier for the trade associated with this signal.
        leg_id (int): Identifier for the leg (part of a multi-leg strategy).
        weight (float): Weight of the trade signal relative to the strategy's allocation.
        quantity (Union[int, float]): The number of instruments to trade.
        limit_price (Optional[float]): Price for a LIMIT order. Required for OrderType.LIMIT.
        aux_price (Optional[float]): Trigger price for a STOPLOSS order. Required for OrderType.STOPLOSS.
    """

    instrument: int
    order_type: OrderType
    action: Action
    signal_id: int
    # trade_id: int = 0
    # leg_id: int = 0
    weight: float = 0.0
    quantity: float = 0.0
    limit_price: Optional[float] = 0.0
    aux_price: Optional[float] = 0.0

    def __post_init__(self):
        """
        Validates the types and values of the input fields after initialization.

        Raises:
            TypeError: If a field is not of the expected type.
            ValueError: If constraints on values are violated, e.g., negative IDs or prices.
        """
        # Type Check
        if not isinstance(self.instrument, int):
            raise TypeError("'instrument' field must be of type int.")
        if not isinstance(self.order_type, OrderType):
            raise TypeError(
                "'order_type' field must be of type OrderType enum."
            )
        if not isinstance(self.action, Action):
            raise TypeError("'action' field must be of type Action enum.")
        if not isinstance(self.signal_id, int):
            raise TypeError("'signal_id' field must of type int.")
        # if not isinstance(self.leg_id, int):
        # raise TypeError("'leg_id' field must be of type int.")
        if not isinstance(self.quantity, float):
            raise TypeError("'quantity' field must be of type float.")
        if self.order_type == OrderType.LIMIT and not isinstance(
            self.limit_price, float
        ):
            raise TypeError(
                "'limit_price' field must be float for OrderType.LIMIT."
            )
        if self.order_type == OrderType.STOPLOSS and not isinstance(
            self.aux_price, float
        ):
            raise TypeError(
                "'aux_price' field must be float for OrderType.STOPLOSS."
            )

        # Value Constraint
        if self.signal_id <= 0:
            raise ValueError("'signal_id' field must be greater than zero.")
        # if self.leg_id <= 0:
        # raise ValueError("'leg_id' field must must be greater than zero.")
        if self.limit_price and self.limit_price <= 0:
            raise ValueError(
                "'limit_price' field must must be greater than zero."
            )
        if self.aux_price and self.aux_price <= 0:
            raise ValueError(
                "'aux_price' field must must be greater than zero."
            )

    def to_dict(self):
        """
        Converts the SignalInstruction object into a dictionary.

        Returns:
            dict: A dictionary representation of the signal instruction.
        """
        return {
            "ticker": self.instrument,
            "order_type": self.order_type.value,
            "action": self.action.value,
            "signal_id": self.signal_id,
            # "leg_id": self.leg_id,
            "weight": round(self.weight, 4),
            "quantity": self.quantity,
            "limit_price": (self.limit_price if self.limit_price else ""),
            "aux_price": self.aux_price if self.aux_price else "",
        }

    def to_mbn(self, ticker: str) -> mbn.SignalInstructions:
        """
        Converts the SignalInstruction object into a binary structure
        (mbn.SignalInstructions).

        Args:
            ticker (str): The ticker or instrument identifier as a string.

        Returns:
            mbn.SignalInstructions: The binary-compatible signal structure.
        """

        return mbn.SignalInstructions(
            ticker=ticker,
            order_type=self.order_type.value,
            action=self.action.value,
            trade_id=self.signal_id,
            leg_id=self.signal_id,
            weight=int(self.weight * PRICE_FACTOR),
            quantity=int(self.quantity * PRICE_FACTOR),
            limit_price=str(self.limit_price) if self.limit_price else "",
            aux_price=str(self.aux_price) if self.aux_price else "",
        )

    def to_order(self) -> Optional[BaseOrder]:
        """
        Converts the signal into its corresponding order object.

        Returns:
            BaseOrder: A specific order type (MarketOrder, LimitOrder, StopLoss)
                       based on the order_type attribute.
        """
        if self.order_type == OrderType.MARKET:
            return MarketOrder(
                self.instrument,
                self.signal_id,
                self.action,
                self.quantity,
            )
        elif self.order_type == OrderType.LIMIT:
            if self.limit_price:
                return LimitOrder(
                    self.instrument,
                    self.signal_id,
                    self.action,
                    self.quantity,
                    self.limit_price,
                )
        elif self.order_type == OrderType.STOPLOSS:
            if self.aux_price:
                return StopLoss(
                    self.instrument,
                    self.signal_id,
                    self.action,
                    self.quantity,
                    self.aux_price,
                )

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the SignalInstruction.

        Returns:
            str: A formatted string with the signal's details.
        """
        return (
            f"Instrument: {self.instrument}, "
            f"Order Type: {self.order_type.name}, "
            f"Action: {self.action.name}, "
            # f"Trade ID: {self.trade_id}, "
            f"Signal ID: {self.signal_id}, "
            f"Weight: {self.weight}, "
            f"Quantity: {self.quantity}, "
            f"Limit Price: {self.limit_price if self.limit_price else ''}, "
            f"Aux Price:  {self.aux_price if self.aux_price else ''}"
        )

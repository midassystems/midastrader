from dataclasses import dataclass, field
from typing import Optional, TypedDict


class OrderStatus(TypedDict):
    """
    A TypedDict representing the order status details received from the broker.

    Attributes:
        permId (int): Permanent identifier of the order.
        clientId (int): Client identifier.
        orderId (int): Unique order identifier.
        parentId (int): Parent order identifier for multi-leg orders.
        filled (float): Total quantity of the order that has been filled.
        remaining (float): Quantity of the order that remains unfilled.
        avgFillPrice (float): Average price at which the order has been filled.
        lastFillPrice (float): Price of the most recent fill.
        whyHeld (str): Reason why the order is held.
        mktCapPrice (float): Market cap price for the order.
    """

    permId: int
    clientId: int
    orderId: int
    parentId: int
    filled: float
    remaining: float
    avgFillPrice: float
    permId: int
    parentId: int
    lastFillPrice: float
    clientId: int
    whyHeld: str
    mktCapPrice: float


@dataclass
class ActiveOrder:
    """
    Represents an active order with details such as order ID, action, price, and status.

    Attributes:
        permId (int): Permanent identifier of the order.
        clientId (int): Client identifier for the order.
        orderId (int): Unique identifier for the order.
        parentId (int): Identifier for the parent order in multi-leg strategies.
        status (str): The current status of the order (e.g., 'PendingSubmit', 'Filled').
        account (Optional[str]): Account associated with the order.
        instrument (Optional[int]): Instrument ID for the order.
        secType (Optional[str]): Security type (e.g., 'STK', 'OPT').
        exchange (Optional[str]): Exchange where the order is placed.
        action (Optional[str]): Action to perform (e.g., 'BUY', 'SELL').
        orderType (Optional[str]): Type of the order (e.g., 'MKT', 'LMT').
        totalQty (Optional[float]): Total quantity of the order.
        cashQty (Optional[float]): Cash quantity (if applicable).
        lmtPrice (Optional[float]): Limit price for limit orders.
        auxPrice (Optional[float]): Auxiliary price for stop orders.
        filled (Optional[float]): Total filled quantity.
        remaining (Optional[float]): Remaining unfilled quantity.
        avgFillPrice (Optional[float]): Average price of filled orders.
        lastFillPrice (Optional[float]): Price of the most recent fill.
        whyHeld (Optional[str]): Reason the order is being held.
        mktCapPrice (Optional[float]): Market cap price for the order.
    """

    permId: int
    clientId: int
    orderId: int
    parentId: int
    status: str  # Options : PendingSubmit, PendingCancel PreSubmitted, Submitted, Cancelled, Filled, Inactive
    account: Optional[str] = field(default=None)
    instrument: Optional[int] = field(default=None)
    secType: Optional[str] = field(default=None)
    exchange: Optional[str] = field(default=None)
    action: Optional[str] = field(default=None)
    orderType: Optional[str] = field(default=None)
    totalQty: Optional[float] = field(default=None)
    cashQty: Optional[float] = field(default=None)
    lmtPrice: Optional[float] = field(default=None)
    auxPrice: Optional[float] = field(default=None)
    filled: Optional[float] = field(default=None)
    remaining: Optional[float] = field(default=None)
    avgFillPrice: Optional[float] = field(default=None)
    lastFillPrice: Optional[float] = field(default=None)
    whyHeld: Optional[str] = field(default=None)
    mktCapPrice: Optional[float] = field(default=None)

    def update_status(self, order_status: OrderStatus):
        """
        Updates the order details based on an OrderStatus dictionary.

        Args:
            order_status (OrderStatus): A dictionary containing the updated order status.

        Example:
            status_update = {
                "filled": 50.0,
                "remaining": 50.0,
                "avgFillPrice": 100.5
            }
            active_order.update_status(status_update)
        """
        for field_name, val in order_status.items():
            setattr(self, field_name, val)

    def update(self, new_details: "ActiveOrder"):
        """
        Updates the current order with the values from another `ActiveOrder` instance.

        Args:
            new_details (ActiveOrder): An instance of ActiveOrder containing new values.

        Example:
            updated_order = ActiveOrder(orderId=1, filled=50.0, remaining=50.0)
            current_order.update(updated_order)
        """
        for field_name in self.__dataclass_fields__:
            new_value = getattr(new_details, field_name)
            if new_value is not None:
                setattr(self, field_name, new_value)

    def to_dict(self):
        """
        Converts the ActiveOrder object into a dictionary representation.

        Returns:
            dict: A dictionary containing all the attributes of the ActiveOrder instance.

        Example:
            order_dict = active_order.to_dict()
        """
        return {
            "permId": self.permId,
            "clientId": self.clientId,
            "orderId": self.orderId,
            "parentId": self.parentId,
            "account": self.account,
            "instrument": self.instrument,
            "secType": self.secType,
            "exchange": self.exchange,
            "action": self.action,
            "orderType": self.orderType,
            "totalQty": self.totalQty,
            "cashQty": self.cashQty,
            "lmtPrice": self.lmtPrice,
            "auxPrice": self.auxPrice,
            "status": self.status,
            "filled": self.filled,
            "remaining": self.remaining,
            "avgFillPrice": self.avgFillPrice,
            "lastFillPrice": self.lastFillPrice,
            "whyHeld": self.whyHeld,
            "mktCapPrice": self.mktCapPrice,
        }

    def pretty_print(self, indent: str = "") -> str:
        """
        Returns a formatted string representation of the ActiveOrder instance.

        Args:
            indent (str): Optional indentation string for formatting.

        Returns:
            str: A human-readable string representation of the order.

        Example:
            print(active_order.pretty_print(indent="  "))
        """
        return (
            # f"{indent}permId: {self.permId}\n"
            # f"{indent}clientId: {self.clientId}\n"
            f"{indent}orderId: {self.orderId}\n"
            # f"{indent}parentId: {self.parentId}\n"
            # f"{indent}account: {self.account}\n"
            f"{indent}instrument: {self.instrument}\n"
            # f"{indent}secType: {self.secType}\n"
            # f"{indent}exchange: {self.exchange}\n"
            f"{indent}action: {self.action}\n"
            f"{indent}orderType: {self.orderType}\n"
            f"{indent}totalQty: {self.totalQty}\n"
            # f"{indent}cashQty: {self.cashQty}\n"
            f"{indent}lmtPrice: {self.lmtPrice}\n"
            f"{indent}auxPrice: {self.auxPrice}\n"
            f"{indent}status: {self.status}\n"
            f"{indent}filled: {self.filled}\n"
            f"{indent}remaining: {self.remaining}\n"
            f"{indent}avgFillPrice: {self.avgFillPrice}\n"
            f"{indent}lastFillPrice: {self.lastFillPrice}\n"
            f"{indent}whyHeld: {self.whyHeld}\n"
            # f"{indent}mktCapPrice: {self.mktCapPrice}\n"
        )

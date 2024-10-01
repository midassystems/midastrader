from dataclasses import dataclass, field
from typing import Optional, TypedDict


class OrderStatus(TypedDict):
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
        for field_name, val in order_status.items():
            setattr(self, field_name, val)

    def update(self, new_details: "ActiveOrder"):
        """Update the current order with the values from the new order."""
        for field_name in self.__dataclass_fields__:
            new_value = getattr(new_details, field_name)
            if new_value is not None:
                setattr(self, field_name, new_value)

    def to_dict(self):
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

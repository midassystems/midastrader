from typing import TypedDict

class ActiveOrder(TypedDict):
    permId: int
    clientId: int
    orderId: int
    parentId: int 
    account: str
    symbol: str
    secType: str
    exchange: str
    action: str 
    orderType: str
    totalQty: float
    cashQty: float
    lmtPrice: float
    auxPrice: float
    status: str     # Options : PendingSubmit, PendingCancel PreSubmitted, Submitted, Cancelled, Filled, Inactive 
    filled: str
    remaining: float
    avgFillPrice: float
    lastFillPrice: float 
    whyHeld: str 
    mktCapPrice: float
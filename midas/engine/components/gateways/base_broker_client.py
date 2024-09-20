from abc import ABC, abstractmethod
from midas.engine.events import OrderEvent, ExecutionEvent

class BaseBrokerClient(ABC):
    def __init__(self):
        pass

    @abstractmethod 
    def on_order(self, event: OrderEvent):
        pass

    # Backtest
    def on_execution(self, event: ExecutionEvent):
        pass

    def eod_update(self):
        pass

    def liquidate_positions(self):
        pass

    def update_equity_value(self):
        pass
    
    # Live
    def request_account_summary(self):
        pass

    def connect(self):
        pass



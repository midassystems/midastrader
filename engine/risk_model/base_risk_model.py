from engine.observer import Observer, Subject, EventType
from engine.order_book import OrderBook
from engine.portfolio import PortfolioServer

class BaseRiskModel(Observer, Subject):
    def __init__(self ):
        Subject.__init__(self)  # Initialize subject part

    def update(self, subject, event_type: EventType, data=None):
        # Handle updates from PortfolioServer and OrderBook
        if isinstance(subject, PortfolioServer) or isinstance(subject, OrderBook):
            self.evaluate_risk()

    def evaluate_risk(self):
        # Placeholder for risk evaluation logic
        # self.logger.info("Evaluating risk...")
        # After evaluating, notify observers about the risk update
        # self.notify(EventType.RISK_MODEL_UPDATE, self.current_risk_level)/
        pass

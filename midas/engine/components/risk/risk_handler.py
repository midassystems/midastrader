from typing import Type
from midas.engine.components.order_book import OrderBook
from midas.engine.components.portfolio_server import PortfolioServer
from midas.engine.components.observer import Observer, Subject, EventType
from midas.engine.components.risk import BaseRiskModel


class RiskHandler(Observer, Subject):
    def __init__(self, risk_model_class: Type[BaseRiskModel]):
        """
        Initialize RiskHandler with a specific risk model class.

        Parameters:
        - risk_model_class (Type[BaseRiskModel]): The class for the risk model to be instantiated.
        """
        if not risk_model_class or not issubclass(
            risk_model_class, BaseRiskModel
        ):
            raise TypeError("Risk model wrong type.")

        # Initialize subject part
        Subject.__init__(self)
        self.risk_model = risk_model_class()

    def update(
        self, subject: Subject, event_type: EventType, data: dict = None
    ):
        """
        Handle updates from subjects and delegate risk evaluation to the risk model.

        Parameters:
        - subject (Subject): The subject sending the update.
        - event_type (EventType): The type of event.
        - data (dict): The data related to the event.
        """
        if isinstance(subject, (PortfolioServer, OrderBook)):
            # Forward relevant data to the risk model
            risk_evaluation_result = self.risk_model.evaluate_risk(
                {"subject": subject, "event_type": event_type, "data": data}
            )
            self.handle_risk_update(risk_evaluation_result)

    def handle_risk_update(self, risk_data: dict):
        """
        Process the risk update received from the risk model.

        Parameters:
        - risk_data (dict): Data related to the risk update.
        """
        # Implement logic to handle risk updates,
        # e.g., send data to a dashboard, log, or take action.
        print(f"Risk update received: {risk_data}")


# class BaseRiskModel(Observer, Subject):
#     def __init__(self ):
#         Subject.__init__(self)  # Initialize subject part

#     def update(self, subject, event_type: EventType, data=None):
#         # Handle updates from PortfolioServer and OrderBook
#         if isinstance(subject, PortfolioServer) or isinstance(subject, OrderBook):
#             self.evaluate_risk()

#     def evaluate_risk(self):
#         # Placeholder for risk evaluation logic
#         # self.logger.info("Evaluating risk...")
#         # After evaluating, notify observers about the risk update
#         # self.notify(EventType.RISK_MODEL_UPDATE, self.current_risk_level)/
#         pass

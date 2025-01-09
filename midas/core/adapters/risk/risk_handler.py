from typing import Type

# from midas.core.order_book import OrderBook
# from midas.core.portfolio import PortfolioServer
from .base_risk_model import BaseRiskModel


class RiskHandler:
    """
    A handler for managing and evaluating risks using a specified risk model.

    This class observes subjects like `PortfolioServer` or `OrderBook` and
    evaluates risks using the provided risk model class. It also acts as a
    subject to notify observers about risk updates.

    Attributes:
        risk_model (BaseRiskModel): An instance of the provided risk model class.

    Methods:
        update(subject, event_type, data=None):
            Handle updates from observed subjects and delegate risk evaluation
            to the risk model.
        handle_risk_update(risk_data):
            Process the evaluated risk data.
    """

    def __init__(self, risk_model_class: Type[BaseRiskModel]):
        """
        Initialize RiskHandler with a specific risk model class.

        Args:
            risk_model_class (Type[BaseRiskModel]): The class for the risk model to be instantiated.

        Raises:
            TypeError: If the provided risk model class is not a subclass of `BaseRiskModel`.
        """
        return


#         if not risk_model_class or not issubclass(
#             risk_model_class, BaseRiskModel
#         ):
#             raise TypeError("Risk model wrong type.")
#
#         # Initialize subject part
#         # Subject.__init__(self)
#         self.risk_model = risk_model_class()
#
#     def update(
#         self,
#         # subject: Subject,
#         # event_type: EventType,
#         data: dict = None,
#     ) -> None:
#         """
#         Handle updates from observed subjects and delegate risk evaluation to the risk model.
#
#         Args:
#             subject (Subject): The subject sending the update (e.g., `PortfolioServer` or `OrderBook`).
#             event_type (EventType): The type of event triggering the update.
#             data (dict, optional): Additional data related to the event. Defaults to None.
#         """
#         if isinstance(subject, (PortfolioServer, OrderBook)):
#             # Forward relevant data to the risk model
#             risk_evaluation_result = self.risk_model.evaluate_risk(
#                 {"subject": subject, "event_type": event_type, "data": data}
#             )
#             self.handle_risk_update(risk_evaluation_result)
#
#     def handle_risk_update(self, risk_data: dict):
#         """
#         Process the risk update received from the risk model.
#
#         Args:
#             risk_data (dict): Data related to the risk update.
#         """
#         # Implement logic to handle risk updates,
#         # e.g., send data to a dashboard, log, or take action.
#         print(f"Risk update received: {risk_data}")

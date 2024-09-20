import importlib.util
from typing import Type
from abc import ABC, abstractmethod

# from midas.engine.components.order_book import OrderBook
# from midas.engine.components.portfolio_server import PortfolioServer
# from midas.engine.components.observer import Observer, Subject, EventType


class BaseRiskModel(ABC):
    """
    Abstract base class for all risk models.
    Responsible for evaluating risk based on provided data.
    """

    @abstractmethod
    def evaluate_risk(self, data: dict) -> dict:
        """
        Evaluate the risk based on the provided data.

        Parameters:
        - data (dict): The data to evaluate risk from.

        Returns:
        - dict: The result of the risk evaluation.
        """
        pass


def load_risk_class(module_path: str, class_name: str) -> Type[BaseRiskModel]:
    """
    Dynamically loads a risk class from a given module path and class name.
    """
    spec = importlib.util.spec_from_file_location("module.name", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    risk_class = getattr(module, class_name)
    if not issubclass(risk_class, BaseRiskModel):
        raise ValueError(
            f"Risk class {class_name} is not a subclass of BaseRiskModel."
        )
    return risk_class

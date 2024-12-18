import importlib.util
from typing import Type
from abc import ABC, abstractmethod


class BaseRiskModel(ABC):
    """
    Abstract base class for all risk models.

    This class defines the interface for risk models, requiring them
    to implement the `evaluate_risk` method. It provides a foundation
    for different types of risk models used in the system.
    """

    @abstractmethod
    def evaluate_risk(self, data: dict) -> dict:
        """
        Evaluate the risk based on the provided data.

        Args:
            data (dict): The data to evaluate risk from.

        Returns:
            dict: The result of the risk evaluation, including any
            relevant metrics or status.

        Raises:
            NotImplementedError: If the method is not implemented by
            a subclass.
        """
        pass


def load_risk_class(module_path: str, class_name: str) -> Type[BaseRiskModel]:
    """
    Dynamically loads a risk class from a given module path and class name.

    This function uses Python's `importlib` module to load a specified
    risk class dynamically at runtime. It ensures the class is a
    subclass of `BaseRiskModel`.

    Args:
        module_path (str): The file path to the module containing the class.
        class_name (str): The name of the class to load.

    Returns:
        Type[BaseRiskModel]: The loaded risk class.

    Raises:
        ValueError: If the specified class is not a subclass of `BaseRiskModel`.
        FileNotFoundError: If the module file cannot be found.
        ImportError: If the module or class cannot be imported.

    Example:
        ```python
        risk_class = load_risk_class("path/to/module.py", "CustomRiskModel")
        risk_instance = risk_class()
        ```
    """
    spec = importlib.util.spec_from_file_location("module.name", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    risk_class = getattr(module, class_name)

    if not issubclass(risk_class, BaseRiskModel):
        raise ValueError(f"{class_name} is not a subclass of BaseRiskModel.")
    return risk_class

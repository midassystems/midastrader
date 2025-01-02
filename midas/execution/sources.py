from enum import Enum

from midas.execution.adaptors.ib.client import IBAdaptor
from midas.execution.adaptors.dummy import DummyAdaptor


class Executors(Enum):
    IB = "interactive_brokers"
    DUMMY = "dummy"

    @staticmethod
    def from_str(value: str) -> "Executors":
        match value.lower():
            case "interactive_brokers":
                return Executors.IB
            case "dummy":
                return Executors.DUMMY
            case _:
                raise ValueError(f"Unknown vendor: {value}")

    def adapter(self):
        """Map the enum to the appropriate adapter class."""
        if self == Executors.IB:
            return IBAdaptor
        elif self == Executors.DUMMY:
            return DummyAdaptor
        else:
            raise ValueError(f"No adapter found for vendor: {self.value}")

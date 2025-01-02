from enum import Enum
from .adaptors.ib import IBAdaptor
from .adaptors.historical import HistoricalAdaptor


class Vendors(Enum):
    DATABENTO = "databento"
    IB = "interactive_brokers"
    HISTORICAL = "historical"

    @staticmethod
    def from_str(value: str) -> "Vendors":
        match value.lower():
            case "databento":
                return Vendors.DATABENTO
            case "interactive_brokers":
                return Vendors.IB
            case "historical":
                return Vendors.HISTORICAL
            case _:
                raise ValueError(f"Unknown vendor: {value}")

    def adapter(self):
        """Map the enum to the appropriate adapter class."""
        if self == Vendors.IB:
            return IBAdaptor
        elif self == Vendors.HISTORICAL:
            return HistoricalAdaptor
        else:
            raise ValueError(f"No adapter found for vendor: {self.value}")

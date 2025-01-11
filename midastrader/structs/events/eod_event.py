from datetime import date
from dataclasses import dataclass, field

from midastrader.structs.events.base import SystemEvent


@dataclass
class EODEvent(SystemEvent):
    """
    Represents an End-of-Day (EOD) event in a trading system.

    An EOD event is triggered at the end of a trading day to initiate tasks such as
    mark-to-market evaluations, portfolio reconciliation, and daily summary calculations.
    This event captures the date for which the end-of-day processing applies.

    Attributes:
        timestamp (date): The date representing the end-of-day moment.
        type (str): Event type, automatically set to 'END-OF-DAY'.
    """

    timestamp: date
    type: str = field(init=False, default="END-OF-DAY")

    def __post_init__(self):
        """
        Validates the `timestamp` attribute to ensure it is of the correct type.

        Raises:
            TypeError: If `timestamp` is not an instance of `datetime.date`.
        """
        # Type Check
        if not isinstance(self.timestamp, date):
            raise TypeError("'timestamp' should be a datetime.date.")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `EODEvent`.

        Returns:
            str: A formatted string showing the event type and timestamp.
        """
        string = f"\n{self.type} EVENT:\n  Timestamp: {self.timestamp}\n"
        return string

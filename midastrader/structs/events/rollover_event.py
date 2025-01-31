from dataclasses import dataclass, field

from mbn import RecordMsg
from midastrader.structs.events.base import SystemEvent
from midastrader.structs.symbol import Symbol


@dataclass
class RolloverEvent(SystemEvent):
    """
    Represents end of historical data stream.

    An EOD event is triggered at the end of a trading day to initiate tasks such as
    mark-to-market evaluations, portfolio reconciliation, and daily summary calculations.
    This event captures the date for which the end-of-day processing applies.

    Attributes:
        timestamp (date): The date representing the end-of-day moment.
        type (str): Event type, automatically set to 'END-OF-DAY'.
    """

    timestamp: int
    symbol: Symbol
    exit_record: RecordMsg
    entry_record: RecordMsg
    type: str = field(init=False, default="END-STREAM")

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the `EODEvent`.

        Returns:
            str: A formatted string showing the event type and timestamp.
        """
        string = f"\n{self.type} EVENT"
        return string

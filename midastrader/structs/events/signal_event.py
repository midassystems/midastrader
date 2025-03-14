import mbinary
from typing import List
from dataclasses import dataclass, field

from midastrader.structs.signal import SignalInstruction
from midastrader.structs.symbol import SymbolMap
from midastrader.structs.events.base import SystemEvent


@dataclass
class SignalEvent(SystemEvent):
    """
    Represents a trading signal event, encapsulating instructions generated by a strategy.

    A `SignalEvent` is the result of analyzing market data, producing one or more instructions
    for executing trades. It includes a timestamp for when the signal was generated, a list
    of trade instructions, and a predefined event type identifier.

    Attributes:
        timestamp (int): The UNIX timestamp in nanoseconds indicating when the signal was generated.
        instructions (List[SignalInstruction]): A list of trade instructions to be executed.
        type (str): The type identifier for this event, always set to 'SIGNAL'.
    """

    timestamp: int
    instructions: List[SignalInstruction]
    type: str = field(init=False, default="SIGNAL")

    def __post_init__(self):
        """
        Post-initialization method to validate the input fields.

        Raises:
            TypeError: If `timestamp` is not an integer, or `instructions` is not a list
                       of `SignalInstruction` instances.
            ValueError: If `instructions` list is empty.
        """
        # Type Check
        if not isinstance(self.timestamp, int):
            raise TypeError("'timestamp' must be of type int.")
        if not isinstance(self.instructions, list):
            raise TypeError("'instructions' must be of type list.")
        if not all(
            isinstance(instruction, SignalInstruction)
            for instruction in self.instructions
        ):
            raise TypeError("All instructions must be SignalInstruction.")

        # Constraint Check
        if len(self.instructions) == 0:
            raise ValueError("'instructions' list cannot be empty.")

    def __str__(self) -> str:
        """
        Converts the SignalEvent into a human-readable string format.

        Returns:
            str: A formatted string representing the event details, including the timestamp
                 and trade instructions.
        """
        instructions_str = "\n    ".join(
            str(instruction) for instruction in self.instructions
        )
        return (
            f"\n{self.type} EVENT:\n"
            f"  Timestamp: {self.timestamp}\n"
            f"  Instructions:\n    {instructions_str}\n"
        )

    def to_mbinary(self, symbols_map: SymbolMap) -> mbinary.Signals:
        """
        Converts the SignalEvent into an `mbinary.Signals` object for compatibility with
        the `mbinary` module.

        Args:
            symbols_map (SymbolMap): A mapping of symbols to their corresponding tickers.

        Returns:
            mbinary.Signals: An `mbinary.Signals` instance containing the timestamp and trade instructions.
        """
        mbinary_instructions = []

        for i in self.instructions:
            ticker = symbols_map.map[i.instrument].midas_ticker
            mbinary_instructions.append(i.to_mbinary(ticker))

        return mbinary.Signals(
            timestamp=int(self.timestamp),
            trade_instructions=mbinary_instructions,
        )

    def to_dict(self) -> dict:
        """
        Converts the SignalEvent into a dictionary format.

        Returns:
            dict: A dictionary containing the event timestamp and serialized instructions.
        """
        return {
            "timestamp": int(self.timestamp),
            "instructions": [trade.to_dict() for trade in self.instructions],
        }

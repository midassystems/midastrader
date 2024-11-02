from typing import List
from dataclasses import dataclass, field
from midas.signal import SignalInstruction
import mbn
from midas.symbol import SymbolMap


@dataclass
class SignalEvent:
    """
    Represents a trading signal event, which includes one or more trading instructions based on strategy analysis.

    This event is critical in algorithmic trading as it triggers actions based on the interpretation of market data.
    It includes details such as the timestamp of the signal, the capital allocated for the trade, and a list of specific
    trading instructions that should be executed.

    Attributes:
    - timestamp (np.uint64): The UNIX timestamp in nanoseconds when the signal was generated.
    - instructions (List[SignalInstruction]): A list of detailed trade instructions.
    - type (str): A string identifier for the event type, set to 'SIGNAL'.
    """

    timestamp: int
    instructions: List[SignalInstruction]
    type: str = field(init=False, default="SIGNAL")

    def __post_init__(self):
        # Type Check
        if not isinstance(self.timestamp, int):
            raise TypeError("'timestamp' field must be of type int.")
        if not isinstance(self.instructions, list):
            raise TypeError("'instructions' field must be of type list.")
        if not all(
            isinstance(instruction, SignalInstruction)
            for instruction in self.instructions
        ):
            raise TypeError(
                "All instructions must be instances of SignalInstruction."
            )

        # Constraint Check
        if len(self.instructions) == 0:
            raise ValueError("'instructions' list cannot be empty.")

    def __str__(self) -> str:
        instructions_str = "\n    ".join(
            str(instruction) for instruction in self.instructions
        )
        return (
            f"\n{self.type} EVENT:\n"
            f"  Timestamp: {self.timestamp}\n"
            f"  Instructions:\n    {instructions_str}\n"
        )

    def to_mbn(self, symbols_map: SymbolMap) -> mbn.Signals:
        mbn_instructions = []

        for i in self.instructions:
            ticker = symbols_map.map[i.instrument].midas_ticker
            mbn_instructions.append(i.to_mbn(ticker))

        return mbn.Signals(
            timestamp=int(self.timestamp),
            trade_instructions=mbn_instructions,
        )

    def to_dict(self):
        return {
            "timestamp": int(self.timestamp),
            "instructions": [trade.to_dict() for trade in self.instructions],
        }

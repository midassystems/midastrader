import random
import pandas as pd
from enum import Enum, auto
from typing import List
from mbinary import OhlcvMsg

from midastrader.structs.symbol import SymbolMap
from midastrader.core.adapters.base_strategy import BaseStrategy
from midastrader.structs.signal import SignalInstruction, OrderType, Action
from midastrader.message_bus import MessageBus
from midastrader.structs.events.market_event import MarketEvent


class Signal(Enum):
    Long = auto()
    Short = auto()
    Exit_Long = auto()
    Exit_Short = auto()


class RandomSignalStrategy(BaseStrategy):
    def __init__(self, symbols_map: SymbolMap, bus: MessageBus):

        # Initialize base
        super().__init__(symbols_map, bus)

        # Parameters
        self.trade_id = 1
        self.trade_allocation = 0.5  # percentage of all cash available
        self.last_signal = None
        self.bars_to_wait = 10  # Wait 10 bars before generating signals
        self.bars_processed = 0  # Track how many bars have been processed

    def handle_event(self, event: MarketEvent):
        """
        Randomly generates entry or exit signals to test the system.
        """
        self.logger.info("IN strategy")
        if isinstance(event.data, OhlcvMsg):
            self.logger.info(event)

            # Increment the counter for each new bar
            self.bars_processed += 1

            # Wait until 10 bars have been processed before generating signals
            if self.bars_processed < self.bars_to_wait:
                self.logger.info(
                    f"Waiting for {self.bars_to_wait - self.bars_processed} more bars."
                )
                return
            # Randomly choose an action
            action_choice = random.choice(
                [
                    Signal.Long,
                    Signal.Short,
                    Signal.Exit_Long,
                    Signal.Exit_Short,
                ]
            )

            # Only generate entry signals if there's no current position
            if action_choice in [Signal.Long, Signal.Short]:
                if not self.portfolio_server.positions:
                    self.last_signal = action_choice
                else:
                    return
            else:
                if self.portfolio_server.positions:
                    self.last_signal = action_choice
                else:
                    return

            # Calculate trade capital
            trade_capital = self.trade_capital(self.trade_allocation)

            # Generate trade instructions
            trade_instructions = self.generate_trade_instructions(
                self.last_signal, trade_capital
            )

            # Send signal
            if trade_instructions:
                self.set_signal(
                    trade_instructions, self.order_book.last_updated
                )
                self.trade_id += 1

    def get_strategy_data(self) -> pd.DataFrame:
        return pd.DataFrame()

    def generate_trade_instructions(
        self,
        signal: Signal,
        trade_capital: float,
    ) -> List[SignalInstruction]:
        """
        Generate trade instructions list.
        """
        quantities = {
            ticker: 1  # Just a simple fixed quantity for testing purposes
            for ticker in self.symbols_map.data_tickers
        }

        trade_instructions = []
        leg_id = 1

        for ticker in self.symbols_map.data_tickers:
            if signal == Signal.Long:
                action = Action.LONG
            elif signal == Signal.Short:
                action = Action.SHORT
            elif signal == Signal.Exit_Long:
                action = Action.SELL
            elif signal == Signal.Exit_Short:
                action = Action.COVER

            trade_instructions.append(
                SignalInstruction(
                    instrument=ticker,  # pyright: ignore
                    order_type=OrderType.MARKET,
                    action=action,
                    weight=1.0,  # Simplified for testing
                    quantity=quantities[ticker],
                )
            )
            leg_id += 1

        return trade_instructions

    def trade_capital(self, trade_allocation: float) -> float:
        trade_capital = self.portfolio_server.capital * trade_allocation
        self.logger.info(f"\nTRADE CAPITAL ALLOCATION : {trade_capital}\n")
        return trade_capital

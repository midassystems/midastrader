import random
import pandas as pd
from enum import Enum, auto
from typing import List
from midas.symbol import SymbolMap
from midas.engine.components.base_strategy import BaseStrategy
from midas.engine.components.portfolio.portfolio_server import PortfolioServer
from midas.engine.components.order_book import OrderBook
from midas.signal import SignalInstruction, OrderType, Action
from midas.engine.components.observer.base import Subject, EventType


class Signal(Enum):
    Long = auto()
    Short = auto()
    Exit_Long = auto()
    Exit_Short = auto()


class RandomSignalStrategy(BaseStrategy):
    def __init__(
        self,
        symbols_map: SymbolMap,
        portfolio_server: PortfolioServer,
        order_book: OrderBook,
    ):
        super().__init__(symbols_map, portfolio_server, order_book)

        # Parameters
        self.trade_id = 1
        self.trade_allocation = 0.5  # percentage of all cash available
        self.last_signal = None
        self.bars_to_wait = 10  # Wait 10 bars before generating signals
        self.bars_processed = 0  # Track how many bars have been processed

    def prepare(self, historical_data: pd.DataFrame) -> None:
        pass

    def handle_event(
        self, subject: Subject, event_type: EventType, event
    ) -> None:
        """
        Randomly generates entry or exit signals to test the system.
        """
        self.logger.info("IN strategy")
        if event_type == EventType.ORDER_BOOK:
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
                if not self.portfolio_server.get_positions:
                    self.last_signal = action_choice
                else:
                    return
            else:
                if self.portfolio_server.get_positions:
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

    def get_strategy_data(self):
        pass

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
            for ticker in self.symbols_map.tickers
        }

        trade_instructions = []
        leg_id = 1

        for ticker in self.symbols_map.tickers:
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
                    ticker=ticker,
                    order_type=OrderType.MARKET,
                    action=action,
                    trade_id=self.trade_id,
                    leg_id=leg_id,
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

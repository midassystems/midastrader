import random
import pandas as pd
from queue import Queue
from enum import Enum, auto
from typing import Dict, List
from midas.symbol import Symbol, SymbolMap
from midas.engine.components.base_strategy import BaseStrategy
from midas.engine.components.portfolio_server import PortfolioServer
from midas.engine.components.order_book import OrderBook
from midas.signal import TradeInstruction, OrderType, Action


class Signal(Enum):
    Long = auto()
    Short = auto()
    Exit_Long = auto()
    Exit_Short = auto()


class RandomSignalStrategy(BaseStrategy):
    def __init__(
        self,
        symbols_map: SymbolMap,
        # historical_data: pd.DataFrame,
        portfolio_server: PortfolioServer,
        logger,
        order_book: OrderBook,
        event_queue: Queue,
    ):
        # Initialize base
        super().__init__(
            symbols_map,
            # historical_data,
            portfolio_server,
            order_book,
            logger,
            event_queue,
        )

        # Parameters
        self.trade_id = 1
        self.trade_allocation = 0.5  # percentage of all cash available
        self.last_signal = None

    def prepare(self, historical_data: pd.DataFrame) -> None:
        pass

    def handle_market_data(self):
        """
        Randomly generates entry or exit signals to test the system.
        """
        # Randomly choose an action
        action_choice = random.choice(
            [Signal.Long, Signal.Short, Signal.Exit_Long, Signal.Exit_Short]
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
            self.set_signal(trade_instructions, self.order_book.last_updated)
            self.trade_id += 1

    def _asset_allocation(self):
        pass

    def _entry_signal(self):
        pass

    def _exit_signal(self):
        pass

    def get_strategy_data(self):
        pass

    # def prepare(self):
    #     pass

    def generate_trade_instructions(
        self,
        signal: Signal,
        trade_capital: float,
    ) -> List[TradeInstruction]:
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
                TradeInstruction(
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

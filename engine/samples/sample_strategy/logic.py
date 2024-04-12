from typing import Dict
from queue import Queue
from datetime import datetime
from core.strategies import BaseStrategy
from core.order_book import OrderBook
from core.base.data import Direction, TradeInstruction
from ibapi.contract import Contract

class ExampleStrategy(BaseStrategy):
    def __init__(self,symbols_map:Dict[str, Contract],order_book:OrderBook,event_queue:Queue):
        """
        Initialize the TestStrategy with required parameters.

        Parameters:
            symbols_map (Dict[str, Contract]): Mapping of symbols to their corresponding contracts.
            event_queue (Queue): Queue for dispatching events.
        """
        super().__init__(order_book, event_queue)
        self.AAPL = symbols_map['AAPL']
        self.MSFT= symbols_map['MSFT']
        self.strategy_allocation = 1.0  # Allocation percentage of total portfolio

    def asset_allocation(self) -> Dict[str, float]:
        """Return allocation percentages for the stocks."""
        return {'AAPL': 0.05, 'MSFT': 0.05}
    
    def entry_signal(self) -> bool:
        """Check conditions for entering a trade."""
        return self.order_book[self.AAPL]['data']['CLOSE'] < self.order_book[self.MSFT]['data']['CLOSE']

    def exit_signal(self) -> bool:
        """Check conditions for exiting a trade."""
        return self.order_book[self.AAPL]['data']['CLOSE'] > self.order_book[self.MSFT]['data']['CLOSE']
    
    def signal_timestamp(self):
        first_key = next(iter(self.order_book))

        if 'TIMESTAMP' in self.order_book[first_key]:
            return self.order_book[first_key]['TIMESTAMP']
        else:
            return datetime.now()

    def handle_market_data(self):
        """
        Process market data and generate trade instructions based on entry and exit signals.

        Parameters:
            data (Dict): Market data.
            timestamp (datetime): Timestamp of the data.
        """
        trade_instructions = []

        if self.current_position is None and self.entry_signal():
            self.current_position = True
            self.trade_id += 1
            trade_instructions.extend([
                TradeInstruction(self.AAPL, Direction.LONG, self.trade_id, 1, self.asset_allocation()['AAPL']),
                TradeInstruction(self.MSFT, Direction.SHORT, self.trade_id, 2, self.asset_allocation()['MSFT'])
            ])

        elif self.current_position and self.exit_signal():
            self.current_position = None
            trade_instructions.extend([
                TradeInstruction(self.AAPL, Direction.SELL, self.trade_id, 1, 1.0),
                TradeInstruction(self.MSFT, Direction.COVER, self.trade_id, 2, 1.0)
            ])

        if trade_instructions:
            self.set_signal(trade_instructions, self.signal_timestamp())


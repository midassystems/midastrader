# strategy_a/config.py
from midas.shared.symbol import Equity, Currency, Venue
from midas.engine.command.config import Config, Mode
from .logic import ExampleStrategy

class ExampleConfig(Config):
    def __init__(self, mode: Mode):    
    
        self.strategy_name = 'example' # must match the directory name
        self.capital = 100000
        self.strategy_allocation = 0.5
        self.start_date = "2023-01-01"
        self.end_date = "2024-01-01"
        self.symbols = [
                        Equity(symbol='AAPL', currency=Currency.USD , exchange=Venue.SMART),
                        Equity(symbol='MSFT', currency=Currency.USD , exchange=Venue.SMART)
                        ]
        
        super().__init__(mode)
        self.set_strategy(ExampleStrategy)

        
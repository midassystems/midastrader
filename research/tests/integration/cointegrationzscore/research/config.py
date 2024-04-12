# strategy_a/config.py
from .logic import Cointegrationzscore

from midas.command import Config, Mode
from midas.symbols import Equity,Future, Currency, Exchange

class CointegrationzscoreConfig(Config):
    def __init__(self, mode: Mode):    
    
        self.strategy_name = 'cointegrationzscore' # must match the directory name
        self.capital = 100000
        self.strategy_allocation = 0.5
        self.start_date = "2018-05-18"
        self.end_date = "2023-01-19"

        self.symbols = [
            Future(symbol="HE.n.0",currency=Currency.USD,exchange=Exchange.SMART,lastTradeDateOrContractMonth="continuous",contractSize=50,tickSize=0.25, initialMargin=4564.17),
            Future(symbol="ZC.n.0",currency=Currency.USD,exchange=Exchange.CME,lastTradeDateOrContractMonth="continuous",contractSize=50,tickSize=0.25, initialMargin=2056.75)
        ]
        
        super().__init__(mode)
        self.set_strategy(Cointegrationzscore)

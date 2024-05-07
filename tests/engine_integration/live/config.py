#config.py
import logging
from .logic import Cointegrationzscore

from midas.engine.command import Config, Mode, Parameters

from midas.shared.market_data import MarketDataType
from midas.shared.symbol import Equity, Future, Currency, Venue, Symbol, ContractUnits, Industry

class CointegrationzscoreConfig(Config):
    def __init__(self, mode: Mode, logger_output="file", logger_level=logging.INFO):  
        session_id = 134

        params = Parameters(
            strategy_name="cointegrationzscore", # must match the directory name
            missing_values_strategy="drop",
            train_start="2024-01-05",
            train_end="2024-01-20",
            test_start="2024-01-21",
            test_end="2024-02-28",
            capital=100000,
            data_type = MarketDataType.BAR,
                        symbols = [
                Future(ticker = "HE",
                        data_ticker = "HE.n.0",
                        currency = Currency.USD,  
                        exchange = Venue.CME,  
                        fees = 0.85,  
                        initialMargin =4564.17,
                        quantity_multiplier=40000,
                        price_multiplier=0.01,
                        product_code="HE",
                        product_name="Lean Hogs",
                        industry=Industry.AGRICULTURE,
                        contract_size=40000,
                        contract_units=ContractUnits.POUNDS,
                        tick_size=0.00025,
                        min_price_fluctuation=10,
                        continuous=False,
                        lastTradeDateOrContractMonth="202405"),
                Future(ticker = "ZC",
                        data_ticker = "ZC.n.0",
                        currency=Currency.USD,
                        exchange=Venue.CBOT,
                        fees=0.85, 
                        quantity_multiplier=5000,
                        price_multiplier=0.01, 
                        initialMargin=2056.75,
                        product_code="ZC",
                        product_name="Corn",
                        industry=Industry.AGRICULTURE,
                        contract_size=5000,
                        contract_units=ContractUnits.BUSHELS,
                        tick_size=0.0025,
                        min_price_fluctuation=12.50,
                        continuous=True,
                        lastTradeDateOrContractMonth="202405")
            ],  
            benchmark=["^GSPC"]
        )  
    
        super().__init__(session_id, mode, params, None, logger_output, logger_level)
        self.set_strategy(Cointegrationzscore)
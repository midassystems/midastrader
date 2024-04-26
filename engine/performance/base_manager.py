import logging
from typing import List, Dict

from engine.events import SignalEvent
# from engine.command import Parameters

from client import DatabaseClient

from shared.trade import Trade
from shared.portfolio import EquityDetails, AccountDetails
from shared.analysis.statistics import PerformanceStatistics


class BasePerformanceManager(PerformanceStatistics):    
    """
    Base class for managing and tracking the performance of trading strategies.
    It collects and logs information about signals, trades, equity changes, and account updates.
    """
    def __init__(self, database: DatabaseClient, logger: logging.Logger, params) -> None:
        """
        Initializes the performance manager with necessary components for tracking and analysis.

        Parameters:
        - database (DatabaseClient): Client for database operations related to performance data.
        - logger (logging.Logger): Logger for recording activity and debugging.
        - params (Parameters): Configuration parameters for the performance manager.
        """
        self.logger = logger
        self.params = params
        self.database = database
        self.signals : List[Dict] = []
        self.trades : List[Dict] = []
        self.equity_value : List[EquityDetails] = []
        self.account_log : List[AccountDetails] = []

    def update_trades(self, trade: Trade):
        """
        Updates and logs the trade history.

        Parameters:
        - trade (Trade): The trade object to be logged.
        """
        if trade not in self.trades:
            self.trades.append(trade)
            self.logger.info(f"\nTrades Updated:\n  {self._output_trades()}")

    def _output_trades(self) -> str:
        """
        Creates a string representation of all trades for logging.

        Returns:
        - str: String representation of all trades.
        """
        return '\n'.join(str(trade) for trade in self.trades)
    
    def update_signals(self, signal: SignalEvent):
        """
        Updates and logs the signal events.

        Parameters:
            signal (SignalEvent): The signal event to be logged.
        """
        self.signals.append(signal.to_dict()) 
        self.logger.info(f"\nSignals Updated: {self._output_signals()}")
        
    def _output_signals(self) -> str:
        """
        Creates a string representation of all signals for logging.

        Returns:
        - str: String representation of all signals.
        """
        string = ""
        for signals in self.signals:
            string += f" {signals} \n"
        return string
    
    def update_account_log(self, account_details: AccountDetails):
        """
        Updates and logs the account details.

        Parameters:
        - account_details (AccountDetails): The account details to be logged.
        """
        self.account_log.append(account_details)
        self.logger.info(f"\nAccount Log Updated: {account_details}")
    
    def update_equity(self, equity_details: EquityDetails):
        """
        Updates and logs equity changes.

        Parameters:
        - equity_details (EquityDetails): The equity details to be logged.
        """
        if equity_details not in self.equity_value:
            self.equity_value.append(equity_details)
            self.logger.info(f"\nEquity Updated: {self.equity_value[-1]}")

    def save(self):
        """
        Saves the collected performance data to a database.
        Implemented in the child classes for live and backtest.
        """
        pass

    
        
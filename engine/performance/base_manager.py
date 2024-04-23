import logging
from typing import List, Dict
from datetime import datetime, timezone

from client import DatabaseClient

from engine.events import SignalEvent
from .statistics import PerformanceStatistics

from shared.trade import Trade
from shared.portfolio import EquityDetails, AccountDetails


class BasePerformanceManager(PerformanceStatistics):
    def __init__(self, database:DatabaseClient, logger:logging.Logger, params) -> None:
        self.logger = logger
        self.params = params
        self.database = database
        self.signals : List[Dict] = []
        self.trades : List[Dict] = []
        self.equity_value : List[EquityDetails] = []
        self.account_log : List[AccountDetails] = []


    def update_trades(self, trade: Trade):
        trade_dict = trade.to_dict()
        if trade_dict not in self.trades:
            self.trades.append(trade_dict)
            self.logger.info(f"\nTrades Updated: \n{self._output_trades()}")

    def _output_trades(self):
        string = ""
        for trade in self.trades:
            string += f" {trade} \n"
        return string
    
    def update_signals(self, signal: SignalEvent):
        self.signals.append(signal.to_dict()) 
        self.logger.info(f"\nSignals Updated: {self._output_signals()}")
        
    def _output_signals(self):
        string = ""
        for signals in self.signals:
            string += f" {signals} \n"
        return string
    
    def update_account_log(self, account_details: AccountDetails):
        self.account_log.append(account_details)
        self.logger.info(f"\nAccount Log Updated: {account_details}")
    
    def update_equity(self, equity_details: EquityDetails):
        equity_details['timestamp'] =  datetime.fromtimestamp(equity_details['timestamp'], timezone.utc).isoformat()
        if equity_details not in self.equity_value:
            self.equity_value.append(equity_details)
            self.logger.info(f"\nEquity Updated: {self.equity_value[-1]}")

    
        
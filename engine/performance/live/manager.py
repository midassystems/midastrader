import json
import logging
import numpy as np
import pandas as pd
from decimal import Decimal
from typing import List, Dict
from client import DatabaseClient

from ..base_manager import BasePerformanceManager
from shared.live_session import LiveTradingSession
        
class LivePerformanceManager(BasePerformanceManager):
    def __init__(self, database:DatabaseClient, logger:logging.Logger, params) -> None:
        super().__init__(database, logger, params)
        
        # self.live_summary = LiveTradingSession(database)
        self.trades = {}

    def update_trades(self, trade_id, trade_data):
        # Assuming trade_id is part of trade_data or passed separately
        self.trades[trade_id] = trade_data
        self.logger.info(f"Trade Updated: {trade_id}\nDetails: {trade_data}")

    def update_trade_commission(self, trade_id, commission):
        if trade_id in self.trades:
            self.trades[trade_id]['fees'] = commission
            self.logger.info(f"Commission Updated for Trade {trade_id}: {commission}")
        else:
            self.logger.warning(f"Trade ID {trade_id} not found for commission update.")
            
    def _process_account_snapshot(self, snapshot:dict, prefix:str, combined_data:dict):
        for key, value in snapshot.items():
            # Currency is added without a prefix and only once
            if key == 'Currency':
                combined_data['currency'] = value
            elif key != 'Timestamp':
                combined_data[f'{prefix}_{key}'] = str(round(Decimal(value),4))
            else:
                combined_data[f'{prefix}_timestamp'] = value

    def create_live_session(self):
        combined_data = {}
        self._process_account_snapshot(self.account_log[0], 'start', combined_data)
        self._process_account_snapshot(self.account_log[-1], 'end', combined_data)

        # Create Live Summary Object

        self.live_summary = LiveTradingSession(parameters=self.params.to_dict(),
                                               signal_data=self.signals,
                                               trade_data=list(self.trades.values()),
                                               account_data=[combined_data])

        # j = json.dumps(self.live_summary.to_dict())
        # print(j)

        # Save Live Summary Object
        # response = self.live_summary.save()
        # self.logger.info(f"Live session details saved :\n{response}")


    
        
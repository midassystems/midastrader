import json
import logging
import numpy as np
import pandas as pd
from decimal import Decimal
from typing import List, Dict
from midas.client import DatabaseClient

from ..base_manager import BasePerformanceManager
from midas.shared.live_session import LiveTradingSession
        
class LivePerformanceManager(BasePerformanceManager):
    """
    Manages performance metrics and logs for a live trading session. This class extends
    BasePerformanceManager with functionality specific to managing live trading data.
    """
    def __init__(self, database: DatabaseClient, logger: logging.Logger, params) -> None:
        """
        Initializes the LivePerformanceManager with database access, logging, and configuration parameters.

        Parameters:
        - database (DatabaseClient): Client for database operations.
        - logger (logging.Logger): Logger for recording activity and debugging.
        - params (Parameters): Configuration parameters for the performance manager.
        """
        super().__init__(database, logger, params)
        self.trades = {}

    def update_trades(self, trade_id: str, trade_data: dict) -> None:
        """
        Updates or adds a trade record by its ID.

        Parameters:
        - trade_id (str): The unique identifier for the trade.
        - trade_data (dict): Detailed information about the trade.
        """
        self.trades[trade_id] = trade_data
        self.logger.info(f"Trade Updated: {trade_id}\nDetails: {trade_data}")

    def update_trade_commission(self, trade_id: str, commission: float) -> None:
        """
        Updates the commission for a specific trade by its ID.

        Parameters:
        - trade_id (str): The unique identifier for the trade.
        - commission (float): The commission amount for the trade.
        """
        if trade_id in self.trades:
            self.trades[trade_id]['fees'] = commission
            self.logger.info(f"Commission Updated for Trade {trade_id}: {commission}")
        else:
            self.logger.warning(f"Trade ID {trade_id} not found for commission update.")
            
    def _process_account_snapshot(self, snapshot: dict, prefix: str, combined_data: dict):
        """
        Processes account snapshot data to flatten it into a single dictionary with prefixed keys.

        Parameters:
        - snapshot (dict): The snapshot data from the account.
        - prefix (str): A prefix to apply to the keys in the snapshot to indicate their timing (e.g., 'start' or 'end').
        - combined_data (dict): The dictionary where the processed data will be stored.
        """
        for key, value in snapshot.items():
            # Currency is added without a prefix and only once
            if key == 'Currency':
                combined_data['currency'] = value
            elif key != 'Timestamp':
                combined_data[f'{prefix}_{key}'] = str(round(Decimal(value),4))
            else:
                combined_data[f'{prefix}_timestamp'] = value

    def save(self):
        """
        Processes and saves the collected data from the live trading session into the database.
        """
        combined_data = {}
        self._process_account_snapshot(self.account_log[0], 'start', combined_data)
        self._process_account_snapshot(self.account_log[-1], 'end', combined_data)
        self.logger.info(f"Account Data {combined_data}")

        # Create Live Summary Object
        self.live_summary = LiveTradingSession(parameters=self.params.to_dict(),
                                               signal_data=self.signals,
                                               trade_data=list(self.trades.values()),
                                               account_data=[combined_data])
        
        # Save Live Summary Session 
        response = self.database.create_live_session(self.live_summary)
        self.logger.info(f"Live Session= saved to data base with response : {response}")




    
        
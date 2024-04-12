import json
import logging
import numpy as np
import pandas as pd
from decimal import Decimal
from typing import List, Dict
from client import DatabaseClient

from ..base_manager import BasePerformanceManager

class LiveTradingSession:
    def __init__(self, database_client:DatabaseClient):
        self.database_client = database_client
        
        self.parameters = {}
        self.signal_data = []
        self.trade_data = []
        self.account_data = []
        
    def to_dict(self):
        return {
            "parameters": self.parameters,
            "signals": self.signal_data,
            "trades": self.trade_data,
            "account_data": self.account_data,
        }
    
    def validate_attributes(self):
        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dictionary")
        if not all(isinstance(item, dict) for item in self.trade_data):
            raise ValueError("trade_data must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in self.account_data):
            raise ValueError("account_data must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in self.signal_data):
            raise ValueError("signal_data must be a list of dictionaries")
    
    def save(self):
        try:
            self.validate_attributes()
            response = self.database_client.create_live_session(self.to_dict())
            return response
        except ValueError as e:
            raise ValueError (f"Validation Error: {e}")
        except Exception as e:
            raise Exception(f"Error when saving the live session: {e}")
        
class LivePerformanceManager(BasePerformanceManager):
    def __init__(self, database:DatabaseClient, logger:logging.Logger, params) -> None:
        super().__init__(database, logger, params)
        
        self.live_summary = LiveTradingSession(database)
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
    
    # def calculate_statistics(self):
    #     try:
    #         self.logger.info(self.account_log)
    #         self.logger.info(self.signals)
    #         self.logger.info(self.trades)
    #         stats = {
    #             "ending_equity": self.equity_value[-1]['equity_value'], #TODO : Figure out stats to save
    #             "total_fees" : sum(trade['fees'] for trade in self.trades),
    #             "unrealized_pnl" : 0, 
    #             "realized_pnl" : 0
    #         }        
    #         self.summary_stats.append(stats)
    #         self.logger.info(f"Summary statistics successfully calculated.")

    #     except ValueError as e:
    #         raise ValueError(f"Error while calculcating summary statistics. {e}")
    #     except TypeError as e:
    #         raise TypeError(f"Error while calculcating summary statistics. {e}")
            
    def process_account_snapshot(self, snapshot:dict, prefix:str, combined_data:dict):
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
        self.process_account_snapshot(self.account_log[0], 'start', combined_data)
        self.process_account_snapshot(self.account_log[-1], 'end', combined_data)

        # Create Live Summary Object
        self.live_summary.parameters = self.params.to_dict()
        self.live_summary.trade_data = list(self.trades.values())
        self.live_summary.signal_data = self.signals
        self.live_summary.account_data = [combined_data]

        # j = json.dumps(self.live_summary.to_dict())
        # print(j)

        # Save Live Summary Object
        response = self.live_summary.save()
        self.logger.info(f"Live session details saved :\n{response}")


    
        
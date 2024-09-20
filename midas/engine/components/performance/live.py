import logging
from typing import Dict
from midas.engine.components.base_strategy import BaseStrategy
from midas.engine.components.performance.base import BasePerformanceManager
from midas.engine.config import Parameters
from midas.live_session import LiveTradingSession
from midas.trade import Trade
from midasClient.client import DatabaseClient


class LivePerformanceManager(BasePerformanceManager):
    """
    Manages performance metrics and logs for a live trading session. This class extends
    BasePerformanceManager with functionality specific to managing live trading data.
    """

    def __init__(
        self,
        database: DatabaseClient,
        logger: logging.Logger,
        params: Parameters,
        strategy: BaseStrategy = None,
    ) -> None:
        """
        Initializes the LivePerformanceManager with database access, logging, and configuration parameters.

        Parameters:
        - database (DatabaseClient): Client for database operations.
        - logger (logging.Logger): Logger for recording activity and debugging.
        - params (Parameters): Configuration parameters for the performance manager.
        """
        super().__init__(database, logger, params)
        self.strategy = strategy
        self.trades: Dict[str, Trade] = {}

    def update_trades(self, trade_id: str, trade_data: Trade) -> None:
        """
        Updates or adds a trade record by its ID.

        Parameters:
        - trade_id (str): The unique identifier for the trade.
        - trade_data (dict): Detailed information about the trade.
        """
        self.trades[trade_id] = trade_data
        self.logger.info(
            f"\nTrade Updated:\n{trade_data.pretty_print("  ")}\n"
        )

    def update_trade_commission(
        self, trade_id: str, commission: float
    ) -> None:
        """
        Updates the commission for a specific trade by its ID.

        Parameters:
        - trade_id (str): The unique identifier for the trade.
        - commission (float): The commission amount for the trade.
        """
        if trade_id in self.trades:
            self.trades[trade_id].fees = commission
            self.logger.info(f"Commission Updated : {trade_id}")
            self.logger.info(
                f"\nTrade Updated:\n{self.trades[trade_id].pretty_print("  ")}"
            )
        else:
            self.logger.warning(
                f"Trade ID {trade_id} not found for commission update."
            )

    def save(self):
        """
        Processes and saves the collected data from the live trading session into the database.
        """
        # Create a dictionary of start and end account values
        combined_data = {
            **self.account_log[0].to_dict(prefix="start_"),
            **self.account_log[-1].to_dict(prefix="end_"),
        }
        self.logger.info(f"Account Data {combined_data}")
        for trade in self.trades:
            self.logger.info(trade)

        # Create Live Summary Object
        self.live_summary = LiveTradingSession(
            parameters=self.params.to_dict(),
            signal_data=self.signals,
            trade_data=[trade.to_dict() for _, trade in self.trades.items()],
            account_data=[combined_data],
        )

        # Save Live Summary Session
        response = self.database.create_live_session(self.live_summary)
        self.logger.info(
            f"Live Session= saved to data base with response : {response}"
        )


# def _process_account_snapshot(self, snapshot: dict, prefix: str, combined_data: dict):
#     """
#     Processes account snapshot data to flatten it into a single dictionary with prefixed keys.

#     Parameters:
#     - snapshot (dict): The snapshot data from the account.
#     - prefix (str): A prefix to apply to the keys in the snapshot to indicate their timing (e.g., 'start' or 'end').
#     - combined_data (dict): The dictionary where the processed data will be stored.
#     """
#     print(self.account_log)
#     print(type(snapshot))
#     print(snapshot)
#     for key, value in snapshot.items():
#         self.logger.info(key)
#         self.logger.info(value)
#         # Currency is added without a prefix and only once
#         if key == 'Currency':
#             combined_data['currency'] = value
#         elif key != 'Timestamp':
#             combined_data[f'{prefix}_{key}'] = str(round(Decimal(value),4))
#         else:
#             combined_data[f'{prefix}_timestamp'] = value

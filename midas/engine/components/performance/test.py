import logging
import numpy as np
import pandas as pd
from typing import List, Dict
from midas.trade import Trade
from midas.engine.events import SignalEvent
from quantAnalytics.risk import RiskAnalysis
from midas.engine.components.base_strategy import BaseStrategy
from midas.live_session import LiveTradingSession

# from midas.engine.command.parameters import Parameters
from midas.utils.unix import resample_daily, unix_to_iso
from quantAnalytics.performance import PerformanceStatistics
from midas.account import EquityDetails, Account
from midasClient.client import DatabaseClient
from midas.backtest import Backtest
from midas.engine.components.performance.managers import (
    AccountManager,
    EquityManager,
    TradeManager,
    SignalManager,
)

import math


def replace_nan_inf_in_dict(d):
    for key, value in d.items():
        if isinstance(value, dict):
            # Recursively handle nested dictionaries
            replace_nan_inf_in_dict(value)
        elif isinstance(value, float) and (
            math.isnan(value) or math.isinf(value)
        ):
            d[key] = 0.0


def _convert_timestamp(df: pd.DataFrame, column: str = "timestamp") -> None:
    df[column] = pd.to_datetime(
        df[column].map(lambda x: unix_to_iso(x, "EST"))
    )
    df[column] = df[column].dt.tz_convert("America/New_York")
    df[column] = df[column].dt.tz_localize(None)


class BasePerformanceManager:
    """
    Base class for managing and tracking the performance of trading strategies.
    It collects and logs information about signals, trades, equity changes, and account updates.
    """

    def __init__(
        self, database: DatabaseClient, logger: logging.Logger, params
    ) -> None:
        """
        Initializes the performance manager with necessary components for tracking and analysis.

        Parameters:
        - database (DatabaseClient): Client for database operations related to performance data.
        - logger (logging.Logger): Logger for recording activity and debugging.
        - params (Parameters): Configuration parameters for the performance manager.
        """
        self.trade_manager = TradeManager()
        self.equity_manager = EquityManager()
        self.signal_manager = SignalManager()
        self.account_manager = AccountManager()

        # Variables
        self.logger = logger
        self.params = params
        self.database = database
        self.signals: List[Dict] = []
        self.account_log: List[Account] = []

    def set_strategy(self, strategy: BaseStrategy):
        self.strategy = strategy

    def update_trades(self, trade: Trade):
        """
        Updates and logs the trade history.

        Parameters:
        - trade (Trade): The trade object to be logged.
        """
        self.trade_manager.update_trades(trade)

    def update_signals(self, signal: SignalEvent):
        """
        Updates and logs the signal events.

        Parameters:
        - signal (SignalEvent): The signal event to be logged.
        """
        self.signal_manager.update_signals(signal)

    def update_account_log(self, account_details: Account):
        """
        Updates and logs the account details.

        Parameters:
        - account_details (AccountDetails): The account details to be logged.
        """
        self.account_manager.update_account_log(account_details)

    def update_equity(self, equity_details: EquityDetails):
        """
        Updates and logs equity changes.

        Parameters:
        - equity_details (EquityDetails): The equity details to be logged.
        """
        self.equity_manager.update_equity(equity_details)

    def export_results(self, output_path: str):
        static_stats_df = pd.DataFrame(self.static_stats).T

        params_df = pd.DataFrame(self.params.to_dict())
        params_df["tickers"] = ", ".join(params_df["tickers"])
        params_df = params_df.iloc[0:1]

        columns = ["train_start", "test_start", "train_end", "test_end"]
        for column in columns:
            self._convert_timestamp(params_df, column)
        params_df = params_df.T

        trades_df = pd.DataFrame(self.trades)
        self._convert_timestamp(trades_df)

        aggregated_trades_df = self._aggregate_trades()
        self._convert_timestamp(aggregated_trades_df, "start_date")
        self._convert_timestamp(aggregated_trades_df, "end_date")

        period_timeseries_df = self.period_timeseries_stats.copy()
        self._convert_timestamp(period_timeseries_df)

        daily_timeseries_df = self.daily_timeseries_stats.copy()
        self._convert_timestamp(daily_timeseries_df)

        signals_df = pd.DataFrame(self.signals)
        signals_df = self._flatten_trade_instructions(
            signals_df, "trade_instructions"
        )
        self._convert_timestamp(signals_df)

        # Extract strategy-specific data
        strategy_data = self.strategy.get_strategy_data()

        with pd.ExcelWriter(
            output_path + "output.xlsx", engine="xlsxwriter"
        ) as writer:
            params_df.to_excel(writer, sheet_name="Parameters")
            static_stats_df.to_excel(writer, sheet_name="Static Stats")
            period_timeseries_df.to_excel(
                writer, index=False, sheet_name="Period Timeseries"
            )
            daily_timeseries_df.to_excel(
                writer, index=False, sheet_name="Daily Timeseries"
            )
            trades_df.to_excel(writer, index=False, sheet_name="Trades")
            aggregated_trades_df.to_excel(
                writer, index=False, sheet_name="Aggregated Trades"
            )
            signals_df.to_excel(writer, index=False, sheet_name="Signals")
            strategy_data.to_excel(
                writer, index=False, sheet_name="Strategy Data"
            )

    def save(self, output_path: str = "") -> None:
        """
        Saves the performance data based on the mode (live or backtest).
        """
        # Calculate statistics before saving
        self.calculate_statistics()

        if self.mode == "backtest":
            self._save_backtest(output_path)
        elif self.mode == "live":
            self._save_live(output_path)

    def _save_backtest(self, output_path: str = "") -> None:
        """
        Saves the collected performance data including the backtest configuration, trades, and signals
        to a database or other storage mechanism.
        """
        # Compile Summary Statistics
        print(f"risk free {self.params.risk_free_rate}")
        # Aggregate trades and equity statistics
        trade_stats = self.calculate_trade_statistics()
        equity_stats = self.calculate_equity_statistics(
            self.params.risk_free_rate
        )

        # Combine all statistics into a single dictionary
        all_stats = {**trade_stats, **equity_stats}
        self.static_stats = all_stats

        # Export Results to Excel
        # self.export_results(output_path) #TODO: uncomment, creates excel doc

        # Create Backtest Object
        self.backtest = Backtest(
            name=self.params.backtest_name,
            parameters=self.params.to_dict(),
            static_stats=self.static_stats,
            period_timeseries_stats=self.period_timeseries_stats.to_dict(
                orient="records"
            ),
            daily_timeseries_stats=self.daily_timeseries_stats.to_dict(
                orient="records"
            ),
            trade_data=[trade.to_dict() for trade in self.trades],
            signal_data=self.signals,
        )
        print(self.backtest.to_dict())

        backtest_dict = self.backtest.to_dict()
        # for key, val in backtest_dict["static_stats"][0].items():
        #     print(f"{key}: {type(val)}")
        # backtest_dict.pop("static_stats", None)
        # # If "static_stats" exists, clean it up
        # if "static_stats" in backtest_dict:
        #     replace_nan_inf_in_dict(backtest_dict["static_stats"][0])

        # Save Backtest Object
        response = self.database.create_backtest(backtest_dict)
        self.logger.info(
            f"Backtest saved to data base with response : {response}"
        )

    def _save_live(self):
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

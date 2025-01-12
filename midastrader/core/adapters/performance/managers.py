import mbn
import numpy as np
import pandas as pd
from typing import List, Dict
from quant_analytics.backtest.metrics import Metrics

from midastrader.structs.trade import Trade
from midastrader.structs.events import (
    SignalEvent,
    TradeEvent,
    TradeCommissionEvent,
)
from midastrader.utils.unix import resample_timestamp, unix_to_iso
from midastrader.structs.account import EquityDetails, Account
from midastrader.structs.symbol import SymbolMap
from midastrader.structs.constants import PRICE_FACTOR
from midastrader.utils.logger import SystemLogger


def _convert_timestamp(df: pd.DataFrame, column: str = "timestamp") -> None:
    """
    Converts a Unix timestamp column in a DataFrame to a localized and human-readable timestamp.

    The function converts Unix timestamps in the specified column to ISO 8601 format, adjusts the timezone
    to 'America/New_York', and removes the timezone information for consistency.

    Args:
        df (pd.DataFrame): The DataFrame containing the timestamp column to convert.
        column (str, optional): The name of the column with Unix timestamps. Defaults to "timestamp".

    Returns:
        None: The function modifies the DataFrame in place.
    """
    df[column] = pd.to_datetime(
        df[column].map(lambda x: unix_to_iso(x, "EST"))
    )
    df[column] = df[column].dt.tz_convert("America/New_York")
    df[column] = df[column].dt.tz_localize(None)


class TradeManager:
    """
    Manages and tracks trade-related operations, including updates, commissions,
    aggregations, and performance statistics.
    """

    def __init__(self, logger: SystemLogger):
        """
        Initializes the TradeManager.

        Args:
            logger (SystemLogger): Logger for recording trade updates and calculations.

        Attributes:
            trades (Dict[str, Trade]): A dictionary storing trades with their IDs as keys.
            logger (SystemLogger): Logger for recording trade operations.
        """
        self.trades: Dict[str, Trade] = {}
        self.logger = logger

    def update_trades(self, event: TradeEvent) -> None:
        """
        Updates or adds a trade record by its ID.

        Args:
            trade_id (str): The unique identifier for the trade.
            trade_data (Trade): Trade object containing trade details.
        """
        self.trades[event.trade_id] = event.trade
        self.logger.debug(
            f"\nTrade Updated:\n{event.trade.pretty_print("  ")}\n"
        )
        self.logger.debug(self.trades)

    def update_trade_commission(self, event: TradeCommissionEvent) -> None:
        """
        Updates the commission for a specific trade by its ID.

        Args:
            trade_id (str): The unique identifier for the trade.
            commission (float): The commission amount for the trade.

        Raises:
            KeyError: If the trade ID does not exist in the trades dictionary.
        """
        self.logger.info(f"{event.trade_id}{event.commission}")
        if event.trade_id in self.trades:
            self.trades[event.trade_id].fees = event.commission
            self.logger.debug(f"Commission Updated : {event.trade_id}")
            self.logger.debug(
                f"\nTrade Updated:\n{self.trades[event.trade_id].pretty_print("  ")}"
            )
        else:
            self.logger.warning(
                f"Trade ID {event.trade_id} not found for commission update."
            )

    def _output_trades(self) -> str:
        """
        Generates a string representation of all trades for logging.

        Returns:
            str: String representation of all trades.
        """
        string = ""
        for trade in self.trades:
            string += f"{trade.pretty_print("  ")}\n"
        return string

    def _aggregate_trades(self) -> pd.DataFrame:
        """
        Aggregates trade data into a structured DataFrame for analysis.

        Returns:
            pd.DataFrame: Aggregated trade statistics including entry and exit values, fees, and PnL.
        """
        if not self.trades:
            return pd.DataFrame()  # Return an empty DataFrame for consistency

        df = pd.DataFrame(self.trades.values())

        # Group by trade_id to calculate aggregated values
        aggregated = df.groupby("trade_id").agg(
            {
                "timestamp": ["first", "last"],
                "trade_value": [
                    (
                        "entry_value",
                        lambda x: x[
                            df["action"].isin(["LONG", "SHORT"])
                        ].sum(),
                    ),
                    (
                        "exit_value",
                        lambda x: x[
                            df["action"].isin(["SELL", "COVER"])
                        ].sum(),
                    ),
                ],
                "trade_cost": [
                    (
                        "entry_value",
                        lambda x: x[
                            df["action"].isin(["LONG", "SHORT"])
                        ].sum(),
                    ),
                    (
                        "exit_value",
                        lambda x: x[
                            df["action"].isin(["SELL", "COVER"])
                        ].sum(),
                    ),
                ],
                "fees": "sum",  # Sum of all fees for each trade group
            }
        )

        # Simplify column names after aggregation
        aggregated.columns = [
            "start_date",
            "end_date",
            "entry_value",
            "exit_value",
            "entry_cost",
            "exit_cost",
            "fees",
        ]

        # Calculate percentage gain/loss based on the entry value
        aggregated["gain/loss"] = (
            aggregated["exit_value"] + aggregated["entry_value"]
        ) * -1

        # Calculate Profit and Loss (PnL)
        aggregated["pnl"] = (
            aggregated["exit_value"] + aggregated["entry_value"]
        ) * -1 + aggregated["fees"]

        aggregated["pnl_percentage"] = (
            aggregated["pnl"] / aggregated["entry_cost"]
        )  # * 100

        # Reset index to make 'trade_id' a column again
        aggregated.reset_index(inplace=True)

        return aggregated

    def calculate_trade_statistics(self) -> Dict[str, float]:
        """
        Calculates trade statistics, such as total trades, average profit, and profitability ratios.

        Returns:
            Dict[str, float]: A dictionary of calculated trade statistics.
        """
        trades_df = self._aggregate_trades()
        trades_pnl = trades_df["pnl"].to_numpy()
        trades_pnl_percent = trades_df["pnl_percentage"].to_numpy()

        return {
            "total_trades": self.total_trades(trades_pnl),
            "total_winning_trades": int(self.total_winning_trades(trades_pnl)),
            "total_losing_trades": int(self.total_losing_trades(trades_pnl)),
            "avg_profit": float(self.avg_profit(trades_pnl)),
            "avg_profit_percent": float(
                self.avg_profit_percent(trades_pnl_percent)
            ),
            "avg_gain": float(self.avg_gain(trades_pnl)),
            "avg_gain_percent": float(
                self.avg_gain_percent(trades_pnl_percent)
            ),
            "avg_loss": float(self.avg_loss(trades_pnl)),
            "avg_loss_percent": float(
                self.avg_loss_percent(trades_pnl_percent)
            ),
            "profitability_ratio": float(self.profitability_ratio(trades_pnl)),
            "profit_factor": float(self.profit_factor(trades_pnl)),
            "profit_and_loss_ratio": float(
                self.profit_and_loss_ratio(trades_pnl)
            ),
            "total_fees": round(float(trades_df["fees"].sum()), 4),
        }

    def to_mbn(self, symbols_map: SymbolMap) -> List[mbn.Trades]:
        """
        Converts trade data into MBN-compatible format.

        Args:
            symbols_map (SymbolMap): Mapping of instrument symbols to their MBN-compatible tickers.

        Returns:
            List[mbn.Trades]: A list of trades in MBN format.
        """
        mbn_trades = []

        for i in self.trades.values():
            ticker = symbols_map.map[i.instrument].midas_ticker
            mbn_trades.append(i.to_mbn(ticker))

        return mbn_trades

    @property
    def trades_dict(self) -> List[dict]:
        """
        Provides trade data as a list of dictionaries.

        Returns:
            List[dict]: List of trade details in dictionary format.
        """
        return [trade.to_dict() for trade in self.trades.values()]

    @staticmethod
    def total_trades(trades_pnl: np.ndarray) -> int:
        """
        Calculate the total number of trades.

        Args:
            trades_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            int: The total number of trades.
        """
        return len(trades_pnl)

    @staticmethod
    def total_winning_trades(trades_pnl: np.ndarray) -> int:
        """
        Calculate the total number of winning trades.

        Args:
            trades_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            int: The total number of winning trades.
        """
        return np.sum(trades_pnl > 0)

    @staticmethod
    def total_losing_trades(trades_pnl: np.ndarray) -> int:
        """
        Calculate the total number of losing trades.

        Args:
            trades_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            int: The total number of losing trades.
        """
        return np.sum(trades_pnl < 0)

    @staticmethod
    def avg_profit(trade_pnl: np.ndarray) -> float:
        """
        Calculate the average profit across all trades.

        Args:
            trade_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            float: The average profit per trade. Returns 0.0 if there are no trades.
        """
        net_profit = trade_pnl.sum()
        total_trades = len(trade_pnl)
        return round(net_profit / total_trades, 4) if total_trades > 0 else 0.0

    @staticmethod
    def avg_profit_percent(trade_pnl_percent: np.ndarray) -> float:
        """
        Calculate the average profit percentage across all trades.

        Args:
            trade_pnl_percent (np.ndarray): Array of profit percentage values for all trades.

        Returns:
            float: The average profit percentage. Returns 0.0 if there are no trades.
        """
        total_trades = len(trade_pnl_percent)
        return round(trade_pnl_percent.mean(), 4) if total_trades > 0 else 0.0

    @staticmethod
    def avg_gain(trades_pnl: np.ndarray) -> float:
        """
        Calculate the average gain of winning trades.

        Args:
            trades_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            float: The average gain of winning trades. Returns 0.0 if there are no winning trades.
        """
        winning_trades = trades_pnl[trades_pnl > 0]
        return (
            round(winning_trades.mean(), 4) if winning_trades.size > 0 else 0.0
        )

    @staticmethod
    def avg_gain_percent(trade_pnl_percent: np.ndarray) -> float:
        """
        Calculate the average gain percentage of winning trades.

        Args:
            trade_pnl_percent (np.ndarray): Array of profit percentage values for all trades.

        Returns:
            float: The average gain percentage of winning trades. Returns 0.0 if there are no winning trades.
        """
        winning_trades = trade_pnl_percent[trade_pnl_percent > 0]
        return (
            round(winning_trades.mean(), 4) if winning_trades.size > 0 else 0.0
        )

    @staticmethod
    def avg_loss(trades_pnl: np.ndarray) -> float:
        """
        Calculate the average loss of losing trades.

        Args:
            trades_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            float: The average loss of losing trades. Returns 0.0 if there are no losing trades.
        """
        losing_trades = trades_pnl[trades_pnl < 0]
        return (
            round(losing_trades.mean(), 4) if losing_trades.size > 0 else 0.0
        )

    @staticmethod
    def avg_loss_percent(trade_pnl_percent: np.ndarray) -> float:
        """
        Calculate the average loss of losing trades.

        Args:
            trades_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            float: The average loss of losing trades. Returns 0.0 if there are no losing trades.
        """
        losing_trades = trade_pnl_percent[trade_pnl_percent < 0]
        return (
            round(losing_trades.mean(), 4) if losing_trades.size > 0 else 0.0
        )

    @staticmethod
    def profitability_ratio(trade_pnl: np.ndarray) -> float:
        """
        Calculate the profitability ratio of trades.

        Args:
            trade_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            float: The ratio of winning trades to total trades. Returns 0.0 if there are no trades.
        """
        total_winning_trades = TradeManager.total_winning_trades(trade_pnl)
        total_trades = len(trade_pnl)
        return (
            round(total_winning_trades / total_trades, 4)
            if total_trades > 0
            else 0.0
        )

    @staticmethod
    def profit_factor(trade_pnl: np.ndarray) -> float:
        """
        Calculate the profit factor (gross profits divided by gross losses).

        Args:
            trade_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            float: The profit factor. Returns 0.0 if there are no losses.
        """
        gross_profits = trade_pnl[trade_pnl > 0].sum()
        gross_losses = abs(trade_pnl[trade_pnl < 0].sum())
        return (
            round(gross_profits / gross_losses, 4) if gross_losses > 0 else 0.0
        )

    @staticmethod
    def profit_and_loss_ratio(trade_pnl: np.ndarray) -> float:
        """
        Calculate the ratio of average gain to average loss.

        Args:
            trade_pnl (np.ndarray): Array of profit and loss values for all trades.

        Returns:
            float: The profit and loss ratio. Returns 0.0 if there are no losing trades.
        """
        # Check for any winning trades and calculate avg_win accordingly
        if len(trade_pnl[trade_pnl > 0]) > 0:
            avg_win = trade_pnl[trade_pnl > 0].mean()
        else:
            avg_win = 0.0

        # Check for any losing trades and calculate avg_loss accordingly
        if len(trade_pnl[trade_pnl < 0]) > 0:
            avg_loss = trade_pnl[trade_pnl < 0].mean()
        else:
            avg_loss = 0.0

        # Only perform division if avg_loss is non-zero
        if avg_loss != 0:
            return round(abs(avg_win / avg_loss), 4)

        return 0.0


class EquityManager:
    """
    Manages equity data for a trading strategy, including updates, calculations of returns,
    drawdowns, and generation of performance statistics.

    Attributes:
        equity_value (List[EquityDetails]): List of equity details recorded during trading.
        daily_stats (pd.DataFrame): DataFrame containing daily equity statistics.
        period_stats (pd.DataFrame): DataFrame containing period-specific equity statistics.
        logger (SystemLogger): Logger instance for logging equity updates and calculations.
    """

    def __init__(self, logger: SystemLogger):
        """
        Initializes the EquityManager with a logger instance.

        Args:
            logger (SystemLogger): Logger for recording equity updates and calculations.
        """
        self.equity_value: List[EquityDetails] = []
        self.daily_stats: pd.DataFrame = None
        self.period_stats: pd.DataFrame = None
        self.logger = logger

    def update_equity(self, equity_details: EquityDetails) -> None:
        """
        Updates the equity details and logs the update if not already recorded.

        Args:
            equity_details (EquityDetails): The equity details to be logged.
        """
        if equity_details not in self.equity_value:
            self.equity_value.append(equity_details)
            self.logger.debug(
                f"\nEQUITY UPDATED: \n  {self.equity_value[-1]}\n"
            )
        else:
            self.logger.debug(
                f"Equity update already included ignoring: {equity_details}"
            )

    @property
    def period_stats_mbn(self) -> mbn.TimeseriesStats:
        """
        Converts period statistics to the Midas Binary Notation (MBN) format.

        Returns:
            List[mbn.TimeseriesStats]: List of timeseries statistics in MBN format.
        """
        return [
            mbn.TimeseriesStats(
                timestamp=stat["timestamp"],
                equity_value=int(stat["equity_value"] * PRICE_FACTOR),
                percent_drawdown=int(stat["percent_drawdown"] * PRICE_FACTOR),
                cumulative_return=int(
                    stat["cumulative_return"] * PRICE_FACTOR
                ),
                period_return=int(stat["period_return"] * PRICE_FACTOR),
            )
            for stat in self.period_stats_dict
        ]

    @property
    def daily_stats_mbn(self) -> mbn.TimeseriesStats:
        """
        Converts daily statistics to the Midas Binary Notation (MBN) format.

        Returns:
            List[mbn.TimeseriesStats]: List of daily timeseries statistics in MBN format.
        """
        return [
            mbn.TimeseriesStats(
                timestamp=stat["timestamp"],
                equity_value=int(stat["equity_value"] * PRICE_FACTOR),
                percent_drawdown=int(stat["percent_drawdown"] * PRICE_FACTOR),
                cumulative_return=int(
                    stat["cumulative_return"] * PRICE_FACTOR
                ),
                period_return=int(stat["period_return"] * PRICE_FACTOR),
            )
            for stat in self.daily_stats_dict
        ]

    @property
    def period_stats_dict(self) -> dict:
        """
        Converts period statistics DataFrame to a dictionary.

        Returns:
            dict: Period statistics as a dictionary.
        """
        return self.period_stats.to_dict(orient="records")

    @property
    def daily_stats_dict(self) -> dict:
        """
        Converts daily statistics DataFrame to a dictionary.

        Returns:
            dict: Daily statistics as a dictionary.
        """
        return self.daily_stats.to_dict(orient="records")

    def _calculate_return_and_drawdown(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculates period returns, cumulative returns, and drawdowns for the given equity curve.

        Args:
            data (pd.DataFrame): DataFrame containing equity values with a datetime index.

        Returns:
            pd.DataFrame: DataFrame enhanced with period returns, cumulative returns, and drawdowns.
        """
        equity_curve = data["equity_value"].to_numpy()

        # Adjust daily_return to add a placeholder at the beginning
        period_returns = Metrics.simple_returns(equity_curve)
        period_returns_adjusted = np.insert(period_returns, 0, 0)

        # Adjust rolling_cumulative_return to add a placeholder at the beginning
        cumulative_returns = Metrics.cumulative_returns(equity_curve)
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)

        data["period_return"] = period_returns_adjusted
        data["cumulative_return"] = cumulative_returns_adjusted
        data["percent_drawdown"] = Metrics.drawdown(period_returns_adjusted)

        # Replace NaN with 0 for the first element
        data.fillna(0, inplace=True)
        return data

    def _remove_intermediate_updates(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Removes intermediate updates, retaining only the last equity value for each timestamp.

        Args:
            data (pd.DataFrame): DataFrame containing equity updates with timestamps.

        Returns:
            pd.DataFrame: DataFrame with only the last entry per timestamp.
        """
        # Group by the timestamp and keep the last entry for each group
        data = data.groupby("timestamp").last()
        return data

    def calculate_equity_statistics(
        self,
        risk_free_rate: float = 0.04,
    ) -> Dict[str, float]:
        """
        Calculates key statistics related to the equity curve, including returns and risk metrics.

        Args:
            risk_free_rate (float, optional): Risk-free rate for calculating Sharpe and Sortino ratios.
                Defaults to 0.04.

        Returns:
            Dict[str, float]: A dictionary containing equity statistics such as net profit, total return,
                standard deviation, drawdowns, and ratios.
        """
        raw_equity_df = pd.DataFrame(self.equity_value)
        raw_equity_df.set_index("timestamp", inplace=True)

        # Remove intermediate updates before calculating returns/drawdowns
        raw_equity_df = self._remove_intermediate_updates(raw_equity_df)

        daily_equity_curve = resample_timestamp(
            raw_equity_df.copy(),
            interval="D",
            tz_info="EST",
        )
        self.period_stats = self._calculate_return_and_drawdown(
            raw_equity_df.copy()
        )
        self.period_stats.reset_index(inplace=True)
        self.daily_stats = self._calculate_return_and_drawdown(
            daily_equity_curve.copy()
        )
        self.daily_stats.reset_index(inplace=True)

        raw_equity_curve = raw_equity_df["equity_value"].to_numpy()
        daily_returns = self.daily_stats["period_return"].to_numpy()
        period_returns = self.period_stats["period_return"].to_numpy()
        annualized_return = round(((1 + daily_returns.mean()) ** 252) - 1, 4)

        return {
            "net_profit": float(Metrics.net_profit(raw_equity_curve)),
            "beginning_equity": float(raw_equity_curve[0]),
            "ending_equity": float(raw_equity_curve[-1]),
            "total_return": float(Metrics.total_return(raw_equity_curve)),
            "annualized_return": float(annualized_return),
            "daily_standard_deviation_percentage": float(
                Metrics.standard_deviation(daily_returns)
            ),
            "annual_standard_deviation_percentage": float(
                Metrics.annual_standard_deviation(daily_returns)
            ),
            "max_drawdown_percentage_period": float(
                Metrics.max_drawdown(period_returns)
            ),
            "max_drawdown_percentage_daily": float(
                Metrics.max_drawdown(daily_returns)
            ),
            "sharpe_ratio": float(
                Metrics.sharpe_ratio(daily_returns, risk_free_rate)
            ),
            "sortino_ratio": float(
                Metrics.sortino_ratio(daily_returns, risk_free_rate)
            ),
        }


class AccountManager:
    """
    Manages account details and maintains a log of account updates during trading sessions.

    Attributes:
        account_log (List[Account]): A list of `Account` objects representing the account history.
        logger (SystemLogger): Logger instance for recording updates and logs.
    """

    def __init__(self, logger: SystemLogger):
        """
        Initializes the AccountManager with a logger instance.

        Args:
            logger (SystemLogger): Logger for recording account updates.
        """
        self.account_log: List[Account] = []
        self.logger = logger

    def update_account_log(self, account_details: Account) -> None:
        """
        Updates the account log with the latest account details.

        Args:
            account_details (Account): An `Account` object containing the latest account details.
        """
        self.account_log.append(account_details)

    def _output_account_log(self) -> str:
        """
        Generates a string representation of the account log.

        Returns:
            str: A newline-separated string representation of the account history.
        """
        return "\n".join([str(account) for account in self.account_log])


class SignalManager:
    """
    Manages trading signals, maintaining a log of signal events and providing utilities for
    processing and exporting signal-related data.

    Attributes:
        signals (List[SignalEvent]): A list of recorded signal events.
        logger (SystemLogger): Logger instance for recording updates and logs.
    """

    def __init__(self, logger: SystemLogger):
        """
        Initializes the SignalManager with a logger instance.

        Args:
            logger (SystemLogger): Logger for recording signal updates.
        """
        self.signals: List[SignalEvent] = []
        self.logger = logger

    def update_signals(self, signal: SignalEvent) -> None:
        """
        Updates and logs a signal event.

        Args:
            signal (SignalEvent): The signal event to be added to the log.
        """
        self.signals.append(signal)
        self.logger.debug(f"\nSIGNALS UPDATED: \n{signal}")

    def _output_signals(self) -> str:
        """
        Creates a string representation of all recorded signals for logging purposes.

        Returns:
            str: A formatted string containing all signal events.
        """
        string = ""
        for signals in self.signals:
            string += f"  Timestamp: {signals['timestamp']} \n"
            string += "  Trade Instructions: \n"
            for instruction in signals["instructions"]:
                string += f"    {instruction}\n"
        return string

    def _flatten_trade_instructions(self) -> pd.DataFrame:
        """
        Flattens the nested trade instructions from signal events into a tabular DataFrame format.

        Returns:
            pd.DataFrame: A DataFrame containing individual trade instructions,
                          expanded from the nested signal events.
        """
        signals_dict = [signal.to_dict() for signal in self.signals]

        df = pd.DataFrame(signals_dict)
        column = "instructions"

        # Expand the 'trade_instructions' column into separate rows
        expanded_rows = []
        for _, row in df.iterrows():
            for instruction in row[column]:
                new_row = row.to_dict()
                new_row.update(instruction)
                expanded_rows.append(new_row)
        expanded_df = pd.DataFrame(expanded_rows)

        # Drop the original nested column
        if column in expanded_df.columns:
            expanded_df = expanded_df.drop(columns=[column])
        return expanded_df

    def to_mbn(self, symbols_map: SymbolMap) -> List[mbn.Signals]:
        """
        Converts the recorded signals into the `mbn.Signals` format for further processing.

        Args:
            symbols_map (SymbolMap): A mapping of instrument identifiers to their respective symbols.

        Returns:
            List[mbn.Signals]: A list of signals converted into the `mbn.Signals` format.
        """
        return [signal.to_mbn(symbols_map) for signal in self.signals]

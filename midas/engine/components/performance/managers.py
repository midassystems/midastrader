import numpy as np
import pandas as pd
from typing import List, Dict
from midas.trade import Trade
from midas.engine.events import SignalEvent
from quantAnalytics.risk import RiskAnalysis
from midas.utils.unix import resample_timestamp, unix_to_iso
from quantAnalytics.performance import PerformanceStatistics
from midas.account import EquityDetails, Account
import mbn
from midas.symbol import SymbolMap
from midas.constants import PRICE_FACTOR


def _convert_timestamp(df: pd.DataFrame, column: str = "timestamp") -> None:
    df[column] = pd.to_datetime(
        df[column].map(lambda x: unix_to_iso(x, "EST"))
    )
    df[column] = df[column].dt.tz_convert("America/New_York")
    df[column] = df[column].dt.tz_localize(None)


class TradeManager:
    def __init__(self, logger):
        self.trades: Dict[str, Trade] = {}
        self.logger = logger

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

    def _output_trades(self) -> str:
        """
        Creates a string representation of all trades for logging.

        Returns:
        - str: String representation of all trades.
        """
        string = ""
        for trade in self.trades:
            string += f"{trade.pretty_print("  ")}\n"
        return string

    def _aggregate_trades(self) -> pd.DataFrame:
        """
        Aggregates trade data into a structured DataFrame for analysis.

        Returns:
        - pd.DataFrame: Aggregated trade statistics including entry and exit values, fees, and pnl.
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
        ) * 100

        # Reset index to make 'trade_id' a column again
        aggregated.reset_index(inplace=True)

        return aggregated

    def calculate_trade_statistics(self) -> Dict[str, float]:
        """
        Calculates statistics related to trades and returns them in a dictionary.
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
        mbn_trades = []

        for i in self.trades.values():
            ticker = symbols_map.map[i.instrument].midas_ticker
            mbn_trades.append(i.to_mbn(ticker))

        return mbn_trades

    @property
    def trades_dict(self) -> List[dict]:
        return [trade.to_dict() for trade in self.trades.values()]

    @staticmethod
    def total_trades(trades_pnl: np.ndarray) -> int:
        return len(trades_pnl)

    @staticmethod
    def total_winning_trades(trades_pnl: np.ndarray) -> int:
        return np.sum(trades_pnl > 0)

    @staticmethod
    def total_losing_trades(trades_pnl: np.ndarray) -> int:
        return np.sum(trades_pnl < 0)

    @staticmethod
    def avg_profit(trade_pnl: np.ndarray) -> float:
        net_profit = trade_pnl.sum()
        total_trades = len(trade_pnl)
        return round(net_profit / total_trades, 4) if total_trades > 0 else 0.0

    @staticmethod
    def avg_profit_percent(trade_pnl_percent: np.ndarray) -> float:
        total_trades = len(trade_pnl_percent)
        return round(trade_pnl_percent.mean(), 4) if total_trades > 0 else 0.0

    @staticmethod
    def avg_gain(trades_pnl: np.ndarray) -> float:
        winning_trades = trades_pnl[trades_pnl > 0]
        return (
            round(winning_trades.mean(), 4) if winning_trades.size > 0 else 0.0
        )

    @staticmethod
    def avg_gain_percent(trade_pnl_percent: np.ndarray) -> float:
        winning_trades = trade_pnl_percent[trade_pnl_percent > 0]
        return (
            round(winning_trades.mean(), 4) if winning_trades.size > 0 else 0.0
        )

    @staticmethod
    def avg_loss(trades_pnl: np.ndarray) -> float:
        losing_trades = trades_pnl[trades_pnl < 0]
        return (
            round(losing_trades.mean(), 4) if losing_trades.size > 0 else 0.0
        )

    @staticmethod
    def avg_loss_percent(trade_pnl_percent: np.ndarray) -> float:
        losing_trades = trade_pnl_percent[trade_pnl_percent < 0]
        return (
            round(losing_trades.mean(), 4) if losing_trades.size > 0 else 0.0
        )

    @staticmethod
    def profitability_ratio(trade_pnl: np.ndarray) -> float:
        total_winning_trades = TradeManager.total_winning_trades(trade_pnl)
        total_trades = len(trade_pnl)
        return (
            round(total_winning_trades / total_trades, 4)
            if total_trades > 0
            else 0.0
        )

    @staticmethod
    def profit_factor(trade_pnl: np.ndarray) -> float:
        gross_profits = trade_pnl[trade_pnl > 0].sum()
        gross_losses = abs(trade_pnl[trade_pnl < 0].sum())
        return (
            round(gross_profits / gross_losses, 4) if gross_losses > 0 else 0.0
        )

    @staticmethod
    def profit_and_loss_ratio(trade_pnl: np.ndarray) -> float:
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

    # @staticmethod
    # def profit_and_loss_ratio(trade_pnl: np.ndarray) -> float:
    #     print(trade_pnl)
    #     avg_win = trade_pnl[trade_pnl > 0].mean()
    #     avg_loss = trade_pnl[trade_pnl < 0].mean()
    #     if avg_loss != 0:
    #         return round(abs(avg_win / avg_loss), 4)
    #     return 0.0


class EquityManager:
    def __init__(self, logger):
        self.equity_value: List[EquityDetails] = []
        self.daily_stats: pd.DataFrame = None
        self.period_stats: pd.DataFrame = None
        self.logger = logger

    def update_equity(self, equity_details: EquityDetails):
        """
        Updates and logs equity changes.

        Parameters:
        - equity_details (EquityDetails): The equity details to be logged.
        """
        if equity_details not in self.equity_value:
            self.equity_value.append(equity_details)
            self.logger.info(
                f"\nEQUITY UPDATED: \n  {self.equity_value[-1]}\n"
            )
        else:
            self.logger.info(
                f"Equity update already included ignoring: {equity_details}"
            )

    @property
    def period_stats_mbn(self) -> mbn.TimeseriesStats:

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
        return self.period_stats.to_dict(orient="records")

    @property
    def daily_stats_dict(self) -> dict:
        return self.daily_stats.to_dict(orient="records")

    def _calculate_return_and_drawdown(
        self, data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculates the period returns, cumulative returns, and drawdowns for a given equity curve.

        Parameters:
        - data (pd.DataFrame): DataFrame containing the equity values with a datetime index.

        Returns:
        - pd.DataFrame: The DataFrame enhanced with columns for period returns, cumulative returns, and drawdowns.
        """
        equity_curve = data["equity_value"].to_numpy()

        # Adjust daily_return to add a placeholder at the beginning
        period_returns = PerformanceStatistics.simple_returns(equity_curve)
        period_returns_adjusted = np.insert(period_returns, 0, 0)

        # Adjust rolling_cumulative_return to add a placeholder at the beginning
        cumulative_returns = PerformanceStatistics.cumulative_returns(
            equity_curve
        )
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)

        data["period_return"] = period_returns_adjusted
        data["cumulative_return"] = cumulative_returns_adjusted
        data["percent_drawdown"] = RiskAnalysis.drawdown(
            period_returns_adjusted
        )

        # Replace NaN with 0 for the first element
        data.fillna(0, inplace=True)
        return data

    def _remove_intermediate_updates(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Removes intermediate updates and keeps the last equity value for each timestamp.

        Parameters:
        - data (pd.DataFrame): The dataframe containing equity updates with timestamps.

        Returns:
        - pd.DataFrame: DataFrame with only the last entry per timestamp.
        """
        # Group by the timestamp and keep the last entry for each group
        data = data.groupby("timestamp").last()
        return data

    def calculate_equity_statistics(
        self, risk_free_rate: float = 0.04
    ) -> Dict[str, float]:
        """
        Calculates statistics related to equity curve and returns them in a dictionary.
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

        return {
            "net_profit": float(
                PerformanceStatistics.net_profit(raw_equity_curve)
            ),
            "beginning_equity": float(raw_equity_curve[0]),
            "ending_equity": float(raw_equity_curve[-1]),
            "total_return": float(
                PerformanceStatistics.total_return(raw_equity_curve)
            ),
            "daily_standard_deviation_percentage": float(
                RiskAnalysis.standard_deviation(daily_returns)
            ),
            "annual_standard_deviation_percentage": float(
                RiskAnalysis.annual_standard_deviation(daily_returns)
            ),
            "max_drawdown_percentage_period": float(
                RiskAnalysis.max_drawdown(period_returns)
            ),
            "max_drawdown_percentage_daily": float(
                RiskAnalysis.max_drawdown(daily_returns)
            ),
            "sharpe_ratio": float(
                RiskAnalysis.sharpe_ratio(daily_returns, risk_free_rate)
            ),
            "sortino_ratio": float(
                RiskAnalysis.sortino_ratio(daily_returns, risk_free_rate)
            ),
        }


class AccountManager:
    def __init__(self, logger):
        self.account_log: List[Account] = []
        self.logger = logger

    def update_account_log(self, account_details: Account):
        """
        Updates the account log with the latest account details.
        """
        self.account_log.append(account_details)

    def _output_account_log(self) -> str:
        return "\n".join([str(account) for account in self.account_log])


class SignalManager:
    def __init__(self, logger):
        self.signals: List[SignalEvent] = []
        self.logger = logger

    def update_signals(self, signal: SignalEvent):
        """
        Updates and logs the signal events.

        Parameters:
        - signal (SignalEvent): The signal event to be logged.
        """
        self.signals.append(signal)
        self.logger.info(f"\nSIGNALS UPDATED: \n{signal}")

    def _output_signals(self) -> str:
        """
        Creates a string representation of all signals for logging.

        Returns:
        - str: String representation of all signals.
        """
        string = ""
        for signals in self.signals:
            string += f"  Timestamp: {signals['timestamp']} \n"
            string += "  Trade Instructions: \n"
            for instruction in signals["instructions"]:
                string += f"    {instruction}\n"
        return string

    def _flatten_trade_instructions(self) -> pd.DataFrame:
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
        # signals = self.signals

        return [signal.to_mbn(symbols_map) for signal in self.signals]
        #     for i in signal.instructions:
        #         i["ticker"] = self.symbols_map.map[i["ticker"]].midas_ticker
        #
        # return signals

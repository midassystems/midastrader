import logging
import numpy as np
import pandas as pd
from typing import List, Dict
from midas.shared.trade import Trade
from midas.client import DatabaseClient
from midas.engine.events import SignalEvent
from quantAnalytics.risk import RiskAnalysis
# from midas.engine.command.parameters import Parameters
from midas.shared.utils import resample_daily, unix_to_iso
from quantAnalytics.performance import PerformanceStatistics
from midas.shared.account import EquityDetails, AccountDetails

class TradesManager:
    def __init__(self):
        self.trades : List[Dict] = []

    def _aggregate_trades(self) -> pd.DataFrame:
        """
        Aggregates trade data into a structured DataFrame for analysis.

        Returns:
        - pd.DataFrame: Aggregated trade statistics including entry and exit values, fees, and pnl.
        """
        if not self.trades:
            return pd.DataFrame()  # Return an empty DataFrame for consistency
        
        df = pd.DataFrame(self.trades)

        # Group by trade_id to calculate aggregated values
        aggregated = df.groupby('trade_id').agg({
            'timestamp': ['first', 'last'],
            'trade_value': [
                            ('entry_value', lambda x: x[df['action'].isin(['LONG', 'SHORT'])].sum()),
                            ('exit_value', lambda x: x[df['action'].isin(['SELL', 'COVER'])].sum())
                            ],
            'trade_cost': [
                            ('entry_value', lambda x: x[df['action'].isin(['LONG', 'SHORT'])].sum()),
                            ('exit_value', lambda x: x[df['action'].isin(['SELL', 'COVER'])].sum())
                            ],
            'fees': 'sum'  # Sum of all fees for each trade group
        })

        # Simplify column names after aggregation
        aggregated.columns = ['start_date', 'end_date', 'entry_value', 'exit_value','entry_cost', 'exit_cost', 'fees']

        # Calculate percentage gain/loss based on the entry value
        aggregated['gain/loss'] = (aggregated['exit_value'] + aggregated['entry_value']) * -1  #  aggregated['pnl'] / aggregated['entry_value'].abs()

        # Calculate Profit and Loss (PnL)
        aggregated['pnl'] = (aggregated['exit_value'] + aggregated['entry_value']) * -1 + aggregated['fees']

        aggregated['pnl_percentage'] = (aggregated['pnl']  / aggregated['entry_cost']) * 100

        # Reset index to make 'trade_id' a column again
        aggregated.reset_index(inplace=True)

        return aggregated

    def calculate_trade_statistics(self) -> Dict[str, float]:
        """
        Calculates statistics related to trades and returns them in a dictionary.
        """
        trades_df = self._aggregate_trades()    
        trades_pnl = trades_df["pnl"].to_numpy()
        trades_gain_loss = trades_df["gain/loss"].to_numpy()

        return {
            "total_trades": self.total_trades(trades_pnl),
            "total_winning_trades": self.total_winning_trades(trades_pnl),
            "total_losing_trades": self.total_losing_trades(trades_pnl),
            "avg_trade_profit": self.avg_trade_profit(trades_pnl),
            "avg_win_percentage": self.avg_win(trades_gain_loss),
            "avg_loss_percentage": self.avg_loss(trades_gain_loss),
            "profitability_ratio": self.profitability_ratio(trades_pnl),
            "profit_factor": self.profit_factor(trades_pnl),
            "profit_and_loss_ratio": self.profit_and_loss_ratio(trades_pnl),
            "total_fees": round(trades_df['fees'].sum(), 4),
        }

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
    def avg_win(trades_pnl: np.ndarray) -> float:
        winning_trades = trades_pnl[trades_pnl > 0]
        return round(winning_trades.mean(), 4) if winning_trades.size > 0 else 0.0

    @staticmethod
    def avg_loss(trades_pnl: np.ndarray) -> float:
        losing_trades = trades_pnl[trades_pnl < 0]
        return round(losing_trades.mean(), 4) if losing_trades.size > 0 else 0.0

    @staticmethod
    def profitability_ratio(trade_pnl: np.ndarray) -> float:
        total_winning_trades = TradesManager.total_winning_trades(trade_pnl)
        total_trades = len(trade_pnl)
        return round(total_winning_trades / total_trades, 4) if total_trades > 0 else 0.0

    @staticmethod
    def avg_trade_profit(trade_pnl: np.ndarray) -> float:
        net_profit = trade_pnl.sum()
        total_trades = len(trade_pnl)
        return round(net_profit / total_trades, 4) if total_trades > 0 else 0.0

    @staticmethod
    def profit_factor(trade_pnl: np.ndarray) -> float:
        gross_profits = trade_pnl[trade_pnl > 0].sum()
        gross_losses = abs(trade_pnl[trade_pnl < 0].sum())
        return round(gross_profits / gross_losses, 4) if gross_losses > 0 else 0.0

    @staticmethod
    def profit_and_loss_ratio(trade_pnl: np.ndarray) -> float:
        avg_win = trade_pnl[trade_pnl > 0].mean()
        avg_loss = trade_pnl[trade_pnl < 0].mean()
        if avg_loss != 0:
            return round(abs(avg_win / avg_loss), 4)
        return 0.0
    
class EquityManager:
    def __init__(self):
        self.equity_value : List[EquityDetails] = []
        self.daily_timeseries_stats : pd.DataFrame = None
        self.period_timeseries_stats : pd.DataFrame = None

    def _calculate_return_and_drawdown(self, data:pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the period returns, cumulative returns, and drawdowns for a given equity curve.

        Parameters:
        - data (pd.DataFrame): DataFrame containing the equity values with a datetime index.

        Returns:
        - pd.DataFrame: The DataFrame enhanced with columns for period returns, cumulative returns, and drawdowns.
        """
        equity_curve = data['equity_value'].to_numpy()

        # Adjust daily_return to add a placeholder at the beginning
        period_returns = PerformanceStatistics.simple_returns(equity_curve)
        period_returns_adjusted = np.insert(period_returns, 0, 0)

        # Adjust rolling_cumulative_return to add a placeholder at the beginning
        cumulative_returns = PerformanceStatistics.cumulative_returns(equity_curve)
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)

        data['period_return'] = period_returns_adjusted
        data['cumulative_return'] = cumulative_returns_adjusted
        data['drawdown'] = RiskAnalysis.drawdown(period_returns_adjusted)
        data.fillna(0, inplace=True)  # Replace NaN with 0 for the first element
        return data
    
    def calculate_equity_statistics(self, risk_free_rate: float = 0.04) -> Dict[str, float]:
        """
        Calculates statistics related to equity curve and returns them in a dictionary.
        """
        raw_equity_df = pd.DataFrame(self.equity_value)
        raw_equity_df.set_index("timestamp", inplace=True)

        daily_equity_curve = resample_daily(raw_equity_df.copy(), 'EST')
        self.period_timeseries_stats = self._calculate_return_and_drawdown(raw_equity_df.copy())
        self.period_timeseries_stats.reset_index(inplace=True)
        self.daily_timeseries_stats = self._calculate_return_and_drawdown(daily_equity_curve.copy())
        self.daily_timeseries_stats.reset_index(inplace=True)

        raw_equity_curve = raw_equity_df['equity_value'].to_numpy()
        daily_returns = self.daily_timeseries_stats["period_return"].to_numpy()

        return {
            "net_profit": PerformanceStatistics.net_profit(raw_equity_curve),
            "beginning_equity": raw_equity_curve[0],
            "ending_equity": raw_equity_curve[-1],
            "total_return": PerformanceStatistics.total_return(raw_equity_curve),
            "annual_standard_deviation_percentage": RiskAnalysis.annual_standard_deviation(daily_returns),
            "max_drawdown_percentage": RiskAnalysis.max_drawdown(daily_returns),
            "sharpe_ratio": RiskAnalysis.sharpe_ratio(daily_returns, risk_free_rate),
            "sortino_ratio": RiskAnalysis.sortino_ratio(daily_returns),
        }

class BasePerformanceManager(TradesManager, EquityManager):    
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
        TradesManager.__init__(self)
        EquityManager.__init__(self)
        
        # Variables
        self.logger = logger
        self.params = params
        self.database = database
        self.signals : List[Dict] = []
        self.account_log : List[AccountDetails] = []

    def update_trades(self, trade: Trade):
        """
        Updates and logs the trade history.

        Parameters:
        - trade (Trade): The trade object to be logged.
        """
        # super().update_trades(trade)
        if trade not in self.trades:
            self.trades.append(trade)
            self.logger.info(f"\nTRADES UPDATED:\n{self._output_trades()}")

    def _output_trades(self) -> str:
        """
        Creates a string representation of all trades for logging.

        Returns:
        - str: String representation of all trades.
        """
        string = ""
        for trade in self.trades:
            string += f"  {trade.to_dict()}\n"
        return string 
    
    def update_signals(self, signal: SignalEvent):
        """
        Updates and logs the signal events.

        Parameters:
        - signal (SignalEvent): The signal event to be logged.
        """
        self.signals.append(signal.to_dict()) 
        self.logger.info(f"\nSIGNALS UPDATED: \n{self._output_signals()}")
        
    def _output_signals(self) -> str:
        """
        Creates a string representation of all signals for logging.

        Returns:
        - str: String representation of all signals.
        """
        string = ""
        for signals in self.signals:
            string += f"  Timestamp: {signals['timestamp']} \n"
            string += f"  Trade Instructions: \n"
            for instruction in signals["trade_instructions"]:
                string += f"    {instruction}\n"
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
            self.logger.info(f"\nEQUITY UPDATED: \n  {self.equity_value[-1]}\n")

    def save(self):
        """
        Saves the collected performance data to a database.
        Implemented in the child classes for live and backtest.
        """
        pass

    
        

    # @staticmethod
    # def total_trades(trade_pnl: np.ndarray) -> int:
    #     """
    #     Calculate the total number of trades in the trade PnL array.

    #     Parameters:
    #     - trade_pnl (np.ndarray): Array of trade profit and loss.

    #     Returns:
    #     - int: The total number of trades.
    #     """
    #     return len(trade_pnl)
    
    # @staticmethod
    # def total_winning_trades(trade_pnl: np.ndarray) -> int:
    #     """
    #     Calculate the total number of winning trades in the trade PnL array.

    #     Parameters:
    #     - trade_pnl (np.ndarray): Array of trade profit and loss.

    #     Returns:
    #     - int: The total number of winning trades.
    #     """
    #     return np.sum(trade_pnl > 0)
    
    # @staticmethod
    # def total_losing_trades(trade_pnl: np.ndarray) -> int:
    #     """
    #     Calculate the total number of losing trades in the trade PnL array.

    #     Parameters:
    #     - trade_pnl (np.ndarray): Array of trade profit and loss.

    #     Returns:
    #     - int: The total number of losing trades.
    #     """
    #     return np.sum(trade_pnl < 0)
    
    # @staticmethod
    # def avg_win_dollars(gain_loss: np.ndarray) -> float:
    #     """
    #     Calculate the average return rate of winning trades in the trade gain/loss array.

    #     Parameters:
    #     - gain_loss (np.ndarray): Array of trade gain and loss.

    #     Returns:
    #     - float: The average return rate of winning trades, rounded to four decimal places.
    #              Returns 0 if there are no winning trades.
    #     """
    #     winning_trades = gain_loss[gain_loss > 0]
    #     return round(winning_trades.mean(), 4) if winning_trades.size > 0 else 0.0

    # @staticmethod
    # def avg_loss_dollars(gain_loss: np.ndarray) -> float:
    #     """
    #     Calculate the average return rate of losing trades in the trade gain/loss array.

    #     Parameters:
    #     - gain_loss (np.ndarray): Array of trade gain and loss.

    #     Returns:
    #     - float: The average return rate of losing trades, rounded to four decimal places.
    #              Returns 0 if there are no losing trades.
    #     """
    #     losing_trades = gain_loss[gain_loss < 0]
    #     return round(losing_trades.mean(), 4) if losing_trades.size > 0 else 0.0
    
    # @staticmethod
    # def profitability_ratio(trade_pnl: np.ndarray) -> float:
    #     """
    #     Calculate the profitability ratio of the trades in the trade PnL array.

    #     Parameters:
    #     - trade_pnl (np.ndarray): Array of trade profit and loss.

    #     Returns:
    #     - float: The profitability ratio, rounded to four decimal places. Returns 0.0 if there are
    #              no trades.
    #     """
    #     total_winning_trades = TradesManager.total_winning_trades(trade_pnl)
    #     total_trades = len(trade_pnl)
    #     return round(total_winning_trades / total_trades, 4) if total_trades > 0 else 0.0
    
    # @staticmethod
    # def avg_trade_profit(trade_pnl: np.ndarray) -> float:
    #     """
    #     Calculate the average profit per trade in the trade PnL array.

    #     Parameters:
    #     - trade_pnl (np.ndarray): Array of trade profit and loss.

    #     Returns:
    #     - float: The average profit per trade, rounded to four decimal places. Returns 0 if there
    #              are no trades.
    #     """
    #     net_profit = trade_pnl.sum()
    #     total_trades = len(trade_pnl)
    #     return round(net_profit / total_trades, 4) if total_trades > 0 else 0.0
    
    # @staticmethod
    # def profit_factor(trade_pnl: np.ndarray) -> float:
    #     """
    #     Calculate the Profit Factor.

    #     Parameters:
    #     - trade_pnl (np.ndarray): Array of trade profit and loss.

    #     Returns:
    #     - float: The profit factor, rounded to four decimal places. Returns 0 if there are no trades
    #              or if the gross losses are zero.
    #     """
    #     gross_profits = trade_pnl[trade_pnl > 0].sum()
    #     gross_losses = abs(trade_pnl[trade_pnl < 0].sum())
        
    #     return round(gross_profits / gross_losses, 4) if gross_losses > 0 else 0.0

    # @staticmethod
    # def profit_and_loss_ratio(trade_pnl: np.ndarray) -> float:
    #     """
    #     Calculate the ratio of average winning trade to average losing trade.

    #     Parameters:
    #     - trade_pnl (np.ndarray): Array of trade profit and loss.

    #     Returns:
    #     - float: The ratio of average winning trade to average losing trade, rounded to four decimal
    #              places. Returns 0 if there are no trades or if the average loss is zero.
    #     """
    #     avg_win = trade_pnl[trade_pnl > 0].mean()
    #     avg_loss = trade_pnl[trade_pnl < 0].mean()
        
    #     if avg_loss != 0:
    #         return round(abs(avg_win / avg_loss), 4)
        
    #     return 0.0


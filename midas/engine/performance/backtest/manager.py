import logging
import numpy as np
import pandas as pd
from typing import List, Dict
from midas.client import DatabaseClient

from ..base_manager import BasePerformanceManager

from midas.shared.trade import Trade
from midas.shared.backtest import Backtest
from quantAnalytics.regression import RegressionAnalysis
from quantAnalytics.returns import Returns
from quantAnalytics.risk import RiskAnalysis


class BacktestPerformanceManager(BasePerformanceManager):
    """
    Manages and tracks the performance of trading strategies during backtesting, 
    including detailed statistical analysis and performance metrics.
    """
    def __init__(self, database: DatabaseClient, logger: logging.Logger, params, granularity: str="D"):
        """
        Initializes the performance manager specifically for backtesting purposes with the ability to
        perform granular analysis and logging of trading performance.

        Parameters:
        - database (DatabaseClient): Client for database operations related to performance data.
        - logger (logging.Logger): Logger for recording activity and debugging.
        - params (Parameters): Configuration parameters for the performance manager.
        - granularity (str): The granularity of the data aggregation ('D' for daily, 'H' for hourly, etc.).
        """
        super().__init__(database, logger, params)
        self.static_stats : List[Dict] =  []
        self.regression_stats : List[Dict] = []
        self.timeseries_stats : pd.DataFrame = ()
        self.granularity = granularity  # 'D' for daily, 'H' for hourly, etc.

    def update_trades(self, trade: Trade) -> None:
        """
        Adds and logs a new trade to the list of trades if it's not already present.

        Parameters:
        - trade (Trade): The trade object to be added.
        """
        if trade not in self.trades:
            self.trades.append(trade)
            self.logger.info(f"\nTrades Updated: \n{self._output_trades()}")
            
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
            'cost': [('entry_value', lambda x: x[df['action'].isin(['LONG', 'SHORT'])].sum()),
                    ('exit_value', lambda x: x[df['action'].isin(['SELL', 'COVER'])].sum())],
            'fees': 'sum'  # Sum of all fees for each trade group
        })

        # Simplify column names after aggregation
        aggregated.columns = ['start_date', 'end_date', 'entry_value', 'exit_value', 'fees']

        # Calculate Profit and Loss (PnL)
        aggregated['pnl'] = aggregated['exit_value'] + aggregated['entry_value'] - aggregated['fees']

        # Calculate percentage gain/loss based on the entry value
        aggregated['gain/loss'] = aggregated['pnl'] / aggregated['entry_value'].abs()

        # Reset index to make 'trade_id' a column again
        aggregated.reset_index(inplace=True)

        return aggregated

    def _timestamps_to_datetime(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the 'timestamp' column from Unix nanoseconds to a datetime object and sets it as the index of the DataFrame.

        Parameters:
        - data (pd.DataFrame): DataFrame containing a 'timestamp' column in Unix nanoseconds.

        Returns:
        - pd.DataFrame: The modified DataFrame with 'timestamp' converted to datetime and set as index.
        """
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ns')
        data.set_index('timestamp', inplace=True)
        return data

    def _standardize_to_granularity(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Resamples the DataFrame to the specified granularity (e.g., daily, hourly) based on the 'timestamp' index,
        taking the last value of the specified period. This method is typically used to standardize time series data for further analysis.

        Parameters:
        - data (pd.DataFrame): DataFrame with a datetime index.

        Returns:
        - pd.DataFrame: The resampled DataFrame according to the specified granularity.
        """
        # Resample to the specified granularity, taking the last value of the period
        period_data = data.resample(self.granularity).last()

        # Drop rows with NaN values that might have resulted from resampling
        period_data.dropna(inplace=True)

        return period_data

    def _calculate_return_and_drawdown(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the period returns, cumulative returns, and drawdowns for a given equity curve.

        Parameters:
        - data (pd.DataFrame): DataFrame containing the equity values with a datetime index.

        Returns:
        - pd.DataFrame: The DataFrame enhanced with columns for period returns, cumulative returns, and drawdowns.
        """
        equity_curve = data['equity_value'].to_numpy()

        # Adjust daily_return to add a placeholder at the beginning
        period_returns = Returns.simple_returns(equity_curve)
        period_returns_adjusted = np.insert(period_returns, 0, 0)
        print(period_returns_adjusted)

        # Adjust rolling_cumulative_return to add a placeholder at the beginning
        cumulative_returns = Returns.cumulative_returns(equity_curve)
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)

        data['period_return'] = np.round(period_returns_adjusted, 6)
        data['cumulative_return'] = cumulative_returns_adjusted
        data['drawdown'] = RiskAnalysis.drawdown(period_returns_adjusted)
        data.fillna(0, inplace=True)  # Replace NaN with 0 for the first element
        return data
    
    def calculate_statistics(self, risk_free_rate: float= 0.04):
        """
        Calculates and logs a variety of statistical measures based on the backtest results, including
        regression analysis against a benchmark and time series statistics of returns.

        Parameters:
        - risk_free_rate (float): The risk-free rate to be used in performance calculations.
        """
        # Get Benchmark Data
        data = self.database.get_bar_data(self.params.benchmark, self.params.test_start, self.params.test_end)
        benchmark_data = [{'timestamp': item['timestamp'], 'close': item['close']} for item in data]
        # benchmark_data = self.database.get_benchmark_data(self.params.benchmark, self.params.test_start, self.params.test_end)
        benchmark_df = pd.DataFrame(benchmark_data)
        benchmark_df["close"] = benchmark_df["close"].astype(float)
        benchmark_df= self._timestamps_to_datetime(benchmark_df)
        benchmark_df=benchmark_df.reset_index()
        
        # Aggregate Trades
        aggregated_trades = self._aggregate_trades()

        # Normalize Equity Curve
        raw_equity_df = pd.DataFrame(self.equity_value)
        raw_equity_df = self._timestamps_to_datetime(raw_equity_df)
        standardized_equity_df = self._standardize_to_granularity(raw_equity_df.copy())
        raw_equity_df=raw_equity_df.reset_index()

        # Regression Analysis 
        regression = RegressionAnalysis(raw_equity_df, benchmark_df)
        regression.perform_regression_analysis()
        regression_results = regression.compile_results()
        self.regression_stats.append(regression_results)

        # Calculate Timeseries Statistics
        self.timeseries_stats = self._calculate_return_and_drawdown(standardized_equity_df)
        daily_strategy_returns = regression.strategy_returns.to_frame(name='daily_strategy_return').round(6)
        daily_benchmark_returns = regression.benchmark_returns.to_frame(name=f'daily_benchmark_return').round(6)
        
        # Merge the returns into the timeseries stats DataFrame
        self.timeseries_stats = self.timeseries_stats.join(daily_strategy_returns, how='left')
        self.timeseries_stats = self.timeseries_stats.join(daily_benchmark_returns, how='left')
        self.timeseries_stats.fillna(0, inplace=True)  # Replace NaN with 0 for the first element
        self.timeseries_stats.index = self.timeseries_stats.index.view('int64')
        self.timeseries_stats = self.timeseries_stats.reset_index(names="timestamp")

        # Convert the appropriate equity curve dataframes to numpy arrays for calculations
        raw_equity_curve = raw_equity_df['equity_value'].to_numpy()
        
        try:
            self.validate_trade_log(aggregated_trades)
            stats = {
            # General Statistics
                'net_profit': self.net_profit(aggregated_trades), 
                'total_fees': round(aggregated_trades['fees'].sum(), 4),
                'total_return': Returns.total_return(raw_equity_curve), # raw
                'annual_standard_deviation': RiskAnalysis.annual_standard_deviation(np.array(daily_strategy_returns)), # raw
                'ending_equity': raw_equity_curve[-1], # raw
                'max_drawdown': RiskAnalysis.max_drawdown(np.array(daily_strategy_returns)), # standardized
                'sharpe_ratio': RiskAnalysis.sharpe_ratio(np.array(daily_strategy_returns), risk_free_rate),
            # Trade Statistics
                'total_trades': self.total_trades(aggregated_trades),
                "num_winning_trades":self.total_winning_trades(aggregated_trades), 
                "num_lossing_trades":self.total_losing_trades(aggregated_trades),
                "avg_win_percent":self.avg_win_return_rate(aggregated_trades),
                "avg_loss_percent":self.avg_loss_return_rate(aggregated_trades),
                "percent_profitable":self.profitability_ratio(aggregated_trades),
                "profit_and_loss" :self.profit_and_loss_ratio(aggregated_trades),
                "profit_factor":self.profit_factor(aggregated_trades),
                "avg_trade_profit":self.avg_trade_profit(aggregated_trades),
                'sortino_ratio': RiskAnalysis.sortino_ratio(np.array(daily_strategy_returns)),
            }
            self.static_stats.append(stats)
            self.logger.info(f"Backtest statistics successfully calculated.")
        except ValueError as e:
            raise ValueError(f"Error while calculcating statistics. {e}")
        except TypeError as e:
            raise TypeError(f"Error while calculcating statistics. {e}")

    def save(self) -> None:
        """
        Saves the collected performance data including the backtest configuration, trades, and signals
        to a database or other storage mechanism.
        """
        # Create Backtest Object
        self.backtest = Backtest(parameters=self.params.to_dict(), 
                                 static_stats=self.static_stats,
                                 regression_stats=self.regression_stats,
                                 timeseries_stats=self.timeseries_stats.to_dict(orient='records'),
                                 trade_data=[trade.to_dict() for trade in self.trades],
                                 signal_data=self.signals
                                 )
        
        # Save Backtest Object
        response = self.database.create_backtest(self.backtest)
        self.logger.info(f"Backtest saved to data base with response : {response}")
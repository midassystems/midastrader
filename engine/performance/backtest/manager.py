import json 
import logging
import numpy as np
import pandas as pd
from typing import List, Dict
from client import DatabaseClient

from ..regression import RegressionAnalysis
from ..base_manager import BasePerformanceManager

from shared.trade import Trade
from shared.backtest import Backtest
from shared.portfolio import EquityDetails, AccountDetails


class BacktestPerformanceManager(BasePerformanceManager):
    def __init__(self, database: DatabaseClient, logger: logging.Logger, params, granularity: str="D") -> None:
        super().__init__(database, logger, params)
        # self.backtest = Backtest(database)
        self.static_stats : List[Dict] =  []
        self.regression_stats : List[Dict] = []
        self.timeseries_stats : pd.DataFrame = ()
        self.granularity = granularity  # 'D' for daily, 'H' for hourly, etc.

    def update_trades(self, trade: Trade):
        # trade_dict = trade.to_dict()
        if trade not in self.trades:
            self.trades.append(trade)
            self.logger.info(f"\nTrades Updated: \n{self._output_trades()}")
            
    def _aggregate_trades(self) -> pd.DataFrame:
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

    def _timestamps_to_datetime(self, data: pd.DataFrame):
        """
        Convert the 'timestamp' from Unix nanoseconds to datetime and set as index.
        """
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ns')
        data.set_index('timestamp', inplace=True)
        return data

    def _standardize_to_granularity(self, data: pd.DataFrame, value_column: str):
        """
        Standardizes input DataFrame to the specified granularity and calculates returns.
        Assumes 'timestamp' in data is Unix nanoseconds.
        """
        # Resample to the specified granularity, taking the last value of the period
        period_data = data.resample(self.granularity).last()

        # Drop rows with NaN values that might have resulted from resampling
        period_data.dropna(inplace=True)

        return period_data

    def _calculate_return_and_drawdown(self, data: pd.DataFrame):
        
        equity_curve = data['equity_value'].to_numpy()

        # Adjust daily_return to add a placeholder at the beginning
        period_returns = self.period_return(equity_curve)
        period_returns_adjusted = np.insert(period_returns, 0, 0)

        # Adjust rolling_cumulative_return to add a placeholder at the beginning
        cumulative_returns = self.cumulative_return(equity_curve)
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)

        data['period_return'] = period_returns_adjusted
        data['cumulative_return'] = cumulative_returns_adjusted
        data['drawdown'] = self.drawdown(equity_curve)
        data.fillna(0, inplace=True)  # Replace NaN with 0 for the first element
        return data
    
    def calculate_statistics(self, risk_free_rate: float= 0.04):
        # Get Benchmark Data
        benchmark_data = self.database.get_benchmark_data(self.params.benchmark, self.params.test_start, self.params.test_end)
        benchmark_df = pd.DataFrame(benchmark_data)
        print(benchmark_df)
        benchmark_df["close"] = benchmark_df["close"].astype(float)
        benchmark_df= self._timestamps_to_datetime(benchmark_df)
        benchmark_df=benchmark_df.reset_index()
        
        # Aggregate Trades
        aggregated_trades = self._aggregate_trades()

        # Normalize Equity Curve
        raw_equity_df = pd.DataFrame(self.equity_value)
        raw_equity_df = self._timestamps_to_datetime(raw_equity_df)
        standardized_equity_df = self._standardize_to_granularity(raw_equity_df.copy(), "equity_value")
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
                'total_return':self.total_return(raw_equity_curve), # raw
                # 'annual_standard_deviation': self.annual_standard_deviation(raw_equity_curve), # raw
                'ending_equity': raw_equity_curve[-1], # raw
                'max_drawdown':self.max_drawdown(raw_equity_curve), # standardized

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
                'sortino_ratio': self.sortino_ratio(aggregated_trades),
            }
            self.static_stats.append(stats)
            self.logger.info(f"Backtest statistics successfully calculated.")
        except ValueError as e:
            raise ValueError(f"Error while calculcating statistics. {e}")
        except TypeError as e:
            raise TypeError(f"Error while calculcating statistics. {e}")

    def save_backtest(self) -> Backtest:
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
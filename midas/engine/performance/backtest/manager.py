import logging
import numpy as np
import pandas as pd
from typing import List, Dict
from midas.shared.trade import Trade
from midas.client import DatabaseClient
from quantAnalytics.returns import Returns
from midas.shared.backtest import Backtest
from quantAnalytics.risk import RiskAnalysis
from midas.shared.utils import resample_daily, unix_to_iso

from midas.engine.performance import BasePerformanceManager


class BacktestPerformanceManager(BasePerformanceManager):
    """
    Manages and tracks the performance of trading strategies during backtesting, 
    including detailed statistical analysis and performance metrics.
    """
    def __init__(self, database:DatabaseClient, logger:logging.Logger, params):
        """
        Initializes the performance manager specifically for backtesting purposes with the ability to
        perform granular analysis and logging of trading performance.

        Parameters:
        - database (DatabaseClient): Client for database operations related to performance data.
        - logger (logging.Logger): Logger for recording activity and debugging.
        - params (Parameters): Configuration parameters for the performance manager.
        """
        super().__init__(database, logger, params)
        self.static_stats : List[Dict] =  []
        self.daily_timeseries_stats : pd.DataFrame = None
        self.period_timeseries_stats : pd.DataFrame = None

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
        period_returns = Returns.simple_returns(equity_curve)
        period_returns_adjusted = np.insert(period_returns, 0, 0)

        # Adjust rolling_cumulative_return to add a placeholder at the beginning
        cumulative_returns = Returns.cumulative_returns(equity_curve)
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)

        data['period_return'] = np.round(period_returns_adjusted, 6)
        data['cumulative_return'] = cumulative_returns_adjusted
        data['drawdown'] = RiskAnalysis.drawdown(period_returns_adjusted)
        data.fillna(0, inplace=True)  # Replace NaN with 0 for the first element
        return data
    
    def calculate_statistics(self, risk_free_rate:float=0.04):
        """
        Calculates and logs a variety of statistical measures based on the backtest results, including
        regression analysis against a benchmark and time series statistics of returns.

        Parameters:
        - risk_free_rate (float): The risk-free rate to be used in performance calculations.
        """        
        # Aggregate Trades
        aggregated_trades = self._aggregate_trades()

        # Equity Curve
        raw_equity_df = pd.DataFrame(self.equity_value)
        raw_equity_df.set_index("timestamp", inplace=True)

        # Daily Equity Curve
        daily_equity_curve = resample_daily(raw_equity_df.copy(),'EST')

        # Calculate Timeseries Statistics
        self.period_timeseries_stats = self._calculate_return_and_drawdown(raw_equity_df.copy())
        self.period_timeseries_stats.reset_index(inplace=True)
        self.daily_timeseries_stats = self._calculate_return_and_drawdown(daily_equity_curve.copy())
        self.daily_timeseries_stats.reset_index(inplace=True)

        # Convert the appropriate equity curve dataframes to numpy arrays for calculations
        raw_equity_curve = raw_equity_df['equity_value'].to_numpy()
        daily_returns = self.daily_timeseries_stats["period_return"].to_numpy()
        
        try:
            self.validate_trade_log(aggregated_trades)
            stats = {
                # Dollars
                "net_profit": self.net_profit(aggregated_trades), 
                "total_fees": round(aggregated_trades['fees'].sum(), 4),
                "ending_equity": raw_equity_curve[-1], # raw
                "avg_trade_profit":self.avg_trade_profit(aggregated_trades),
                
                # Percentages
                "total_return": Returns.total_return(raw_equity_curve), # raw
                "annual_standard_deviation_percentage": RiskAnalysis.annual_standard_deviation(np.array(daily_returns)), # # may want as period not daily
                "max_drawdown_percentage": RiskAnalysis.max_drawdown(np.array(daily_returns)), # may want as period not daily
                "avg_win_percentage":self.avg_win_return_rate(aggregated_trades),
                "avg_loss_percentage":self.avg_loss_return_rate(aggregated_trades),
                "percent_profitable":self.profitability_ratio(aggregated_trades),
                
                # Real Numbers 
                "total_trades": self.total_trades(aggregated_trades),
                "number_winning_trades":self.total_winning_trades(aggregated_trades), 
                "number_losing_trades":self.total_losing_trades(aggregated_trades),
                "profit_and_loss_ratio" :self.profit_and_loss_ratio(aggregated_trades),
                "profit_factor":self.profit_factor(aggregated_trades),
                "sharpe_ratio": RiskAnalysis.sharpe_ratio(np.array(daily_returns), risk_free_rate),
                "sortino_ratio": RiskAnalysis.sortino_ratio(np.array(daily_returns)),
            }
            self.static_stats.append(stats)
            self.logger.info(f"Backtest statistics successfully calculated.")
        except ValueError as e:
            raise ValueError(f"Error while calculcating statistics. {e}")
        except TypeError as e:
            raise TypeError(f"Error while calculcating statistics. {e}")
        
    def _convert_timestamp(self, df:pd.DataFrame, column:str="timestamp") -> None:
        df[column] = pd.to_datetime(df[column].map(lambda x: unix_to_iso(x, "EST")))
        df[column]  = df[column].dt.tz_convert('America/New_York')
        df[column] = df[column].dt.tz_localize(None)

    def _flatten_trade_instructions(self, df: pd.DataFrame, column:str) -> pd.DataFrame:
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
 
    def export_results(self, output_path:str):
        static_stats_df = pd.DataFrame(self.static_stats).T

        params_df = pd.DataFrame(self.params.to_dict())
        params_df['tickers'] = ', '.join(params_df['tickers'])
        params_df = params_df.iloc[0:1] 
    
        columns  = ["train_start", "test_start", "train_end", "test_end"]
        for column in columns: 
            self._convert_timestamp(params_df, column)
        params_df = params_df.T


        trades_df = pd.DataFrame(self.trades)
        self._convert_timestamp(trades_df)
        
        period_timeseries_df = self.period_timeseries_stats.copy()
        self._convert_timestamp(period_timeseries_df)
    
        daily_timeseries_df = self.daily_timeseries_stats.copy()
        self._convert_timestamp(daily_timeseries_df)

        signals_df = pd.DataFrame(self.signals)
        signals_df = self._flatten_trade_instructions(signals_df, 'trade_instructions')
        self._convert_timestamp(signals_df)

        with pd.ExcelWriter(output_path + 'output.xlsx', engine='xlsxwriter') as writer:
            params_df.to_excel(writer, sheet_name='Parameters')
            static_stats_df.to_excel(writer, sheet_name='Static Stats')
            period_timeseries_df.to_excel(writer, index=False, sheet_name='Period Timeseries')
            daily_timeseries_df.to_excel(writer, index=False, sheet_name='Daily Timeseries')
            trades_df.to_excel(writer, index=False, sheet_name='Trades')
            signals_df.to_excel(writer, index=False, sheet_name='Signals')

    def save(self) -> None:
        """
        Saves the collected performance data including the backtest configuration, trades, and signals
        to a database or other storage mechanism.
        """
        # Export Results to Excel
        self.export_results("")

        # Create Backtest Object
        self.backtest = Backtest(parameters=self.params.to_dict(), 
                                 static_stats=self.static_stats,
                                 period_timeseries_stats=self.period_timeseries_stats.to_dict(orient='records'),
                                 daily_timeseries_stats=self.daily_timeseries_stats.to_dict(orient='records'),
                                 trade_data=[trade.to_dict() for trade in self.trades],
                                 signal_data=self.signals
                                 )
        
        # Save Backtest Object
        response = self.database.create_backtest(self.backtest)
        self.logger.info(f"Backtest saved to data base with response : {response}")
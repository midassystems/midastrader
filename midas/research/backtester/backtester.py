import numpy as np
import pandas as pd
from quantAnalytics.returns import Returns
from quantAnalytics.risk import RiskAnalysis
from midas.research.strategy import BaseStrategy
from quantAnalytics.statistics import TimeseriesTests
from quantAnalytics.performance import PerformanceStatistics

class VectorizedBacktest(PerformanceStatistics):
    """
    A class for conducting vectorized backtesting of trading strategies on historical data.

    This class provides a structured approach to evaluate the performance of trading strategies by simulating trades based on historical price data and calculating key performance metrics. It is designed to be efficient by utilizing vectorized operations, which typically provide better performance over iterative methods for large datasets.

    Attributes:
    - full_data (pd.DataFrame): The complete dataset containing historical price data for one or more securities.
    - strategy (BaseStrategy): An instance of a strategy derived from the BaseStrategy class, which defines the logic for trade signal generation.
    - initial_capital (float): The starting capital for the backtest. Defaults to $10,000.
    - symbols (list): A list of column names from `full_data` representing different securities.
    - equity_curve (pd.Series): A pandas Series representing the equity value over time, updated during the backtest.
    - backtest_data (pd.DataFrame): A DataFrame to store the results of the backtest, including trading signals and performance metrics.

    Methods:
    - setup(): Optional preparation for the backtesting environment, such as loading additional data or configuring parameters.
    - run_backtest(entry_threshold, exit_threshold): Executes the backtest using specified entry and exit thresholds for trading signals.
    - _calculate_equity_curve(): Calculates the equity curve based on trading signals and updates the `equity_curve` attribute.
    - _calculate_metrics(risk_free_rate=0.04): Computes various performance metrics such as the Sharpe Ratio and maximum drawdown.
    """
    def __init__(self, strategy: BaseStrategy, full_data: pd.DataFrame, symbols_map:dict, initial_capital:float=10000, train_ratio:float=0.65):
        """
        Initializes the VectorizedBacktest object with a dataset, a trading strategy, and initial capital.
        
        Parameters:
        - full_data (pandas.DataFrame): A DataFrame containing the full dataset to be used in the backtest.
        - strategy (BaseStrategy): An instance of BaseStrategy that defines the trading logic.
        - initial_capital (float): The initial capital amount in dollars. Defaults to 10,000.
        """
        self.strategy = strategy
        self.symbols_map = symbols_map
        self.initial_capital = initial_capital
        self.train_data, self.test_data = self.split_data(full_data, train_ratio)
        self.summary_stats = {}

    def split_data(self, full_data:pd.DataFrame, train_ratio:float=0.65):
        train_data, test_data = TimeseriesTests.split_data(full_data, train_ratio)
        return train_data, test_data

    def setup(self):
        """
        Prepares the backtesting environment by optionally calling the strategy's prepare method.
        This can include setting up necessary parameters or data within the strategy.
        """
        if hasattr(self.strategy, 'prepare'):
            try:
                self.strategy.prepare(self.train_data.copy())
                print("Strategy preparation completed.")
            except Exception as e:
                raise Exception(f"Error during strategy preparation: {e}")

    def run_backtest(self, position_lag:int) -> pd.DataFrame:
        """
        Executes the backtest by generating trading signals and calculating equity curves based on entry and exit thresholds.

        Parameters:
        - entry_threshold: The threshold to trigger a trade entry.
        - exit_threshold: The threshold to trigger a trade exit.
        - lag (int): The number of periods the entry/exit of a position will be lagged after a signal.
        
        Returns:
        - pandas.DataFrame: A DataFrame containing the backtest results including signals and equity values.
        """

        print("Starting backtest...")
        
        try:
            signals = self.strategy.generate_signals(self.test_data)
            self._calculate_positions(signals, position_lag)
            self._calculate_positions_pnl()
            self._calculate_equity_curve()
            self._calculate_metrics()
            print("Backtest completed successfully.")
            return self.test_data, self.summary_stats
        except Exception as e:
            raise Exception(f"Backtest failed: {e}")


    def _calculate_positions(self, signals:pd.DataFrame, lag:int) -> None:
        """
        Calculates the positions held over the course of the backtest.

        Parameters:
        - signals (pd.DataFrame): DataFrame containing trading signals for each ticker.
        - lag (int): The number of periods the entry/exit of a position will be lagged after a signal.
        """
        for ticker in signals.columns:
            # Position signals are filled forward until changed
            position_column = f'{ticker}_position'
            self.test_data[position_column] = signals[ticker].ffill().shift(lag).fillna(0)
            
            # Retrieve multipliers and weights
            hedge_ratio = abs(self.strategy.weights[ticker])
            quantity_multiplier = self.symbols_map[ticker]['quantity_multiplier']
            price_multiplier = self.symbols_map[ticker]['price_multiplier']
            
            # Calculate the dollar value of each position
            position_value_column = f'{ticker}_position_value'
            self.test_data[position_value_column] = (self.test_data[position_column] * self.test_data[ticker] * 
                                                hedge_ratio * quantity_multiplier * price_multiplier)
    
    def _calculate_positions_pnl(self) -> None:
        pnl_columns = []

        for column in self.test_data.filter(like='_position_value').columns:
            profit_loss_column = column.replace('position_value', 'position_pnl')
            self.test_data[profit_loss_column] = self.test_data[column].diff().fillna(0)

            # Identify the start of a new position (assuming a new position starts when the previous value is 0)
            # Set the P&L to zero at the start of new positions
            new_position_starts = (self.test_data[column] != 0) & (self.test_data[column].shift(1) == 0)
            self.test_data.loc[new_position_starts, profit_loss_column] = 0

            # Identify the end of a position (position value goes to zero)
            # Set the P&L to zero at the end of positions
            position_ends = (self.test_data[column] == 0) & (self.test_data[column].shift(1) != 0)
            self.test_data.loc[position_ends, profit_loss_column] = 0

            # Add the P&L column name to the list
            pnl_columns.append(profit_loss_column)

        # Sum all P&L columns to create a single 'portfolio_pnl' column
        self.test_data['portfolio_pnl'] = self.test_data[pnl_columns].sum(axis=1)

    def _calculate_equity_curve(self) -> None:
        # Initialize the equity_curve column with the initial capital
        self.test_data['equity_value'] = self.initial_capital
        
        # Calculate the equity_curve by cumulatively summing the portfolio_pnl with the initial capital
        self.test_data['equity_value'] = self.test_data['equity_value'].shift(1).fillna(self.initial_capital) + self.test_data['portfolio_pnl'].cumsum()
        
    def _calculate_metrics(self, risk_free_rate:float=0.04) -> None:
        """
        Calculates performance metrics for the backtest including period return, cumulative return, drawdown, and Sharpe ratio.

        Parameters:
        - risk_free_rate (float): The annual risk-free rate used for calculating the Sharpe ratio. Default is 0.04 (4%).
        """
        # Ensure that equity values are numeric and NaNs are handled
        equity_values = pd.to_numeric(self.test_data['equity_value'], errors='coerce').fillna(0)

        # Compute simple and cumulative returns
        period_returns = Returns.simple_returns(equity_values.values)
        period_returns_adjusted = np.insert(period_returns, 0, 0)  # Adjust for initial zero return
        cumulative_returns = Returns.cumulative_returns(equity_values.values)
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)

        # Update DataFrame safely using loc
        self.test_data['period_return'] = period_returns_adjusted
        self.test_data['cumulative_return'] = cumulative_returns_adjusted
        self.test_data['drawdown'] = RiskAnalysis.drawdown(period_returns_adjusted)

        # Calculate summary statistics
        self.summary_stats = {
            "annual_standard_deviation": RiskAnalysis.annual_standard_deviation(period_returns_adjusted),
            "sharpe_ratio": RiskAnalysis.sharpe_ratio(period_returns_adjusted, risk_free_rate),
            "max_drawdown": RiskAnalysis.max_drawdown(period_returns_adjusted), # standardized
            "sortino_ratio": RiskAnalysis.sortino_ratio(period_returns_adjusted),
            "ending_equity": equity_values.values[-1], # raw
        }
        self.test_data.fillna(0, inplace=True) 
import logging
import numpy as np
import pandas as pd

from midas.research.strategy import BaseStrategy

from quantAnalytics.returns import Returns
from quantAnalytics.risk import RiskAnalysis
from quantAnalytics.performance import PerformanceStatistics

logging.basicConfig(level=logging.INFO)

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
    def __init__(self, full_data: pd.DataFrame, strategy: BaseStrategy,  initial_capital: float = 10000):
        """
        Initializes the VectorizedBacktest object with a dataset, a trading strategy, and initial capital.
        
        Parameters:
        - full_data (pandas.DataFrame): A DataFrame containing the full dataset to be used in the backtest.
        - strategy (BaseStrategy): An instance of BaseStrategy that defines the trading logic.
        - initial_capital (float): The initial capital amount in dollars. Defaults to 10,000.
        """
        self.full_data = full_data
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.symbols = full_data.columns.tolist()

        self.equity_curve = None
        self.backtest_data : pd.DataFrame

    def setup(self) -> str:
        """
        Prepares the backtesting environment by optionally calling the strategy's prepare method.
        This can include setting up necessary parameters or data within the strategy.
        
        Returns:
        - str: HTML content generated during the setup process if any.
        """
        html_content = ""
        if hasattr(self.strategy, 'prepare'):
            try:
                html_content = self.strategy.prepare(self.full_data)
                logging.info("Strategy preparation completed and added to the report.")
            except Exception as e:
                raise Exception(f"Error during strategy preparation: {e}")
        return html_content

    def run_backtest(self, entry_threshold: float, exit_threshold: float) -> pd.DataFrame:
        """
        Executes the backtest by generating trading signals and calculating equity curves based on entry and exit thresholds.

        Parameters:
        - entry_threshold: The threshold to trigger a trade entry.
        - exit_threshold: The threshold to trigger a trade exit.
        
        Returns:
        - pandas.DataFrame: A DataFrame containing the backtest results including signals and equity values.
        """

        logging.info("Starting backtest...")
        assert self.full_data is not None, "Full data must be provided before running backtest."
        assert self.strategy is not None, "Strategy must be set before running backtest."
        
        try:
            self.backtest_data = self.strategy.generate_signals(entry_threshold, exit_threshold)
            self._calculate_equity_curve()
            self._calculate_metrics()
            logging.info("Backtest completed successfully.")
        except Exception as e:
            logging.error(f"Backtest failed: {e}")
            raise

        return self.backtest_data

    def _calculate_equity_curve(self) -> None:
        """
        Calculates the equity curve for the backtest by aggregating individual position returns.
        The method updates the 'equity_value' column in the backtest_data DataFrame.
        """
        logging.info("Starting equity curve calculation.")
        
        # Initialize a column for aggregate returns
        self.backtest_data['aggregate_returns'] = 0

        # Iterate through each ticker to calculate individual returns
        for ticker in self.symbols:
            price_column, position_column, returns_column = f'{ticker}', f'{ticker}_position', f'{ticker}_returns'
            try:
                # Calculate daily returns for ticker
                self.backtest_data[returns_column] = self.backtest_data[price_column].pct_change()
                
                # Return for postion if holding
                self.backtest_data[f'{ticker}_position_returns'] = self.backtest_data[returns_column] * self.backtest_data[position_column].shift(1)

                # Aggregate the individual strategy returns into the total returns
                self.backtest_data['aggregate_returns'] += self.backtest_data[f'{ticker}_position_returns']
            except Exception as e:
                logging.error(f"Error processing {ticker}: {e}")

        # Calculate the equity curve from aggregate returns
        self.backtest_data['equity_value'] = (self.backtest_data['aggregate_returns'] + 1).cumprod() * self.initial_capital

        # Fill NaN values for the initial capital in the equity curve
        self.backtest_data['equity_value'] = self.backtest_data['equity_value'].fillna(self.initial_capital)


        logging.info("Equity value calculation completed.")

    def _calculate_metrics(self, risk_free_rate: float= 0.04) -> None:
        """
        Calculates performance metrics for the backtest including period return, cumulative return, drawdown, and Sharpe ratio.

        Parameters:
        - risk_free_rate (float): The annual risk-free rate used for calculating the Sharpe ratio. Default is 0.04 (4%).
        """
        # Assuming self.equity_curve is a pandas Series of cumulative returns
        equity_values_array = self.backtest_data['equity_value'].to_numpy()
        equity_value = equity_values_array.astype(np.float64)
        
        period_returns = Returns.simple_returns(equity_value)
        period_returns_adjusted = np.insert(period_returns, 0, 0)

        # Adjust rolling_cumulative_return to add a placeholder at the beginning
        cumulative_returns = Returns.cumulative_returns(equity_value)
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)
        annual_standard_deviation = RiskAnalysis.annual_standard_deviation(np.array(period_returns_adjusted))
        sharpe_ratio = RiskAnalysis.sharpe_ratio(np.array(period_returns_adjusted)),

        self.backtest_data['period_return'] = period_returns_adjusted
        self.backtest_data['cumulative_return'] = cumulative_returns_adjusted
        self.backtest_data['drawdown'] = RiskAnalysis.drawdown(np.array(period_returns_adjusted))
        self.backtest_data.fillna(0, inplace=True)  # Replace NaN with 0 for the first element

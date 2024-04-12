import logging
import numpy as np
import pandas as pd
from .statistics import PerformanceStatistics
from research.strategy import BaseStrategy

logging.basicConfig(level=logging.INFO)

class VectorizedBacktest(PerformanceStatistics):
    def __init__(self, full_data: pd.DataFrame, strategy: BaseStrategy,  initial_capital: float = 10000):
        self.full_data = full_data
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.symbols = full_data.columns.tolist()

        self.equity_curve = None
        self.backtest_data : pd.DataFrame

    def setup(self) -> None:
        """
        Prepares the backtesting environment by optionally calling the strategy's prepare method if it exists.
        The result is then added to the report generator.
        """
        html_content = ""
        if hasattr(self.strategy, 'prepare'):
            try:
                html_content = self.strategy.prepare(self.full_data)
                logging.info("Strategy preparation completed and added to the report.")
            except Exception as e:
                raise Exception(f"Error during strategy preparation: {e}")
        return html_content

    def run_backtest(self, entry_threshold: float, exit_threshold: float) -> None:
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

    def _calculate_equity_curve(self):
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

    def _calculate_metrics(self, risk_free_rate: float= 0.04):
        # Assuming self.equity_curve is a pandas Series of cumulative returns
        equity_values_array = self.backtest_data['equity_value'].to_numpy()
        equity_value = equity_values_array.astype(np.float64)
        
        period_returns = self.period_return(equity_value)
        period_returns_adjusted = np.insert(period_returns, 0, 0)

        # Adjust rolling_cumulative_return to add a placeholder at the beginning
        cumulative_returns = self.cumulative_return(equity_value)
        cumulative_returns_adjusted = np.insert(cumulative_returns, 0, 0)
        annual_standard_deviation = self.annual_standard_deviation(equity_value)
        sharpe_ratio = self.sharpe_ratio(equity_value),

        self.backtest_data['period_return'] = period_returns_adjusted
        self.backtest_data['cumulative_return'] = cumulative_returns_adjusted
        self.backtest_data['drawdown'] = self.drawdown(equity_value)
        self.backtest_data.fillna(0, inplace=True)  # Replace NaN with 0 for the first element

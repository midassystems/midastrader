import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class PerformanceStatistics:
    @staticmethod
    def validate_trade_log(trade_log: pd.DataFrame):
        # Expected columns and their data types
        expected_columns = {
            'trade_id': 'int64',
            'start_date': 'object',  # Could enforce datetime dtype after initial check
            'end_date': 'object',    # Could enforce datetime dtype after initial check
            'entry_value': 'float64',
            'exit_value': 'float64',
            'fees': 'float64',
            'pnl': 'float64',
            'gain/loss': 'float64'
        }
        
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check for the presence of all expected columns
        missing_columns = [col for col in expected_columns if col not in trade_log.columns]
        if missing_columns:
            raise ValueError(f"Missing columns in trade_log DataFrame: {missing_columns}")
        
        # Check data types of columns
        for column, expected_dtype in expected_columns.items():
            if trade_log[column].dtype != expected_dtype:
                # Attempt to convert column types if not matching
                try:
                    if expected_dtype == 'object' and column in ['start_date', 'end_date']:
                        trade_log[column] = pd.to_datetime(trade_log[column])
                    else:
                        trade_log[column] = trade_log[column].astype(expected_dtype)
                except Exception as e:
                    raise ValueError(f"Error converting {column} to {expected_dtype}: {e}")
        
        return True
    
    # -- General -- 
    @staticmethod
    def net_profit(trade_log: pd.DataFrame):
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0
        
        # Perform calculation if checks pass
        return round(trade_log['pnl'].sum(), 4)
    
    @staticmethod
    def period_return(equity_curve: np.ndarray):
        """
        Calculate period returns from an equity curve.
        
        This function assumes the input equity curve represents period closing values 
        at consistent period intervals. "It calculates the percentage change in value 
        from one period to the next, returning these period returns in decimal format."
        
        Parameters:
        - equity_curve (np.ndarray): An array of  closing equity values. 
        The equity curve should be preprocessed to ensure it represents 
        values at consistent period intervals before being passed to this function.
        
        Returns:
        - np.ndarray: An array of period returns in decimal format.
        """
        if not isinstance(equity_curve, np.ndarray):
            raise TypeError("equity_curve must be a numpy array")
        
        # Check for empty array
        if len(equity_curve) == 0:
            return np.array([0])
        else:
            period_returns_np = np.diff(equity_curve) / equity_curve[:-1] # Calculate period returns using vectorized operations
            return np.around(period_returns_np, decimals=4) 

    @staticmethod
    def cumulative_return(equity_curve: np.ndarray):
        """Returns are in decimal format."""
        if not isinstance(equity_curve, np.ndarray):
            raise TypeError("equity_curve must be a numpy array")
        
        # Check for empty array
        if len(equity_curve) == 0:
            return np.array([0])
        else:
            period_returns = np.diff(equity_curve) / equity_curve[:-1] # Calculate period returns
            cumulative_returns = np.cumprod(1 + period_returns) - 1 # Calculate cumulative returns
            return np.around(cumulative_returns, decimals=4)
        
    @staticmethod
    def total_return(equity_curve:np.ndarray):
        """Returns are in decimal format."""
        return PerformanceStatistics.cumulative_return(equity_curve)[-1]  # Returns the latest cumulative return
    
    @staticmethod
    def drawdown(equity_curve: np.ndarray):
        """Drawdown values are in decimal format."""
        if not isinstance(equity_curve, np.ndarray):
            raise TypeError("equity_curve must be a numpy array")
        
        # Check for empty array
        if len(equity_curve) == 0:
            return np.array([0])
        else:
            rolling_max = np.maximum.accumulate(equity_curve)  # Calculate the rolling maximum
            drawdowns = (equity_curve - rolling_max) / rolling_max  # Calculate drawdowns in decimal format
            return np.around(drawdowns, decimals=4)
        
    @staticmethod
    def max_drawdown(equity_curve:np.ndarray):
        """Drawdown values are in decimal format."""
        drawdowns = PerformanceStatistics.drawdown(equity_curve)
        max_drawdown = np.min(drawdowns)  # Find the maximum drawdown
        return max_drawdown

    @staticmethod
    def annual_standard_deviation(equity_curve:np.ndarray):
        """Calculate the annualized standard deviation of returns from a NumPy array of log returns."""
        if not isinstance(equity_curve, np.ndarray):
            raise TypeError("equity_curve must be a numpy array")
        
        # Check for empty array
        if len(equity_curve) == 0:
            return np.array([0])
        else:
            daily_std_dev = np.std(equity_curve, ddof=1)  # Calculate daily standard deviation
            annual_std_dev = round(daily_std_dev * np.sqrt(252), 4)  # Assuming 252 trading days in a year
            return np.around(annual_std_dev, decimals=4)

    # -- Trades -- 
    @staticmethod
    def total_trades(trade_log: pd.DataFrame):
        return len(trade_log)
    
    @staticmethod
    def total_winning_trades(trade_log:pd.DataFrame):
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0
        else:
            return len(trade_log[trade_log['pnl'] > 0])
    
    @staticmethod
    def total_losing_trades(trade_log:pd.DataFrame):
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0
        else:
            return len(trade_log[trade_log['pnl'] < 0])
    
    @staticmethod
    def avg_win_return_rate(trade_log:pd.DataFrame):
        """Returned value is in decimal format. """
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0
        else:
            winning_trades = round(trade_log[trade_log['pnl'] > 0], 4)
            return np.around(winning_trades['gain/loss'].mean(),decimals=4) if not winning_trades.empty else 0

    @staticmethod
    def avg_loss_return_rate(trade_log:pd.DataFrame):
        """Returned value is in decimal format. """
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0
        else:
            losing_trades = round(trade_log[trade_log['pnl'] < 0],4)
            return np.around(losing_trades['gain/loss'].mean(),decimals=4) if not losing_trades.empty else 0
    
    @staticmethod
    def profitability_ratio(trade_log: pd.DataFrame):
        """Values returned as decimal format."""
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0.0
        else:
            total_winning_trades = PerformanceStatistics.total_winning_trades(trade_log)
            total_trades = len(trade_log)
            return round(total_winning_trades / total_trades, 4) if total_trades > 0 else 0.0
    
    @staticmethod
    def avg_trade_profit(trade_log:pd.DataFrame):
        """Values returned in dollars. """
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0
        else:
            net_profit = PerformanceStatistics.net_profit(trade_log)
            total_trades = len(trade_log)
            return round(net_profit / total_trades,4) if total_trades > 0 else 0
    
    @staticmethod
    def profit_factor(trade_log:pd.DataFrame):
        """Calculate the Profit Factor."""
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0

        gross_profits = trade_log[trade_log['pnl'] > 0]['pnl'].sum()
        gross_losses = abs(trade_log[trade_log['pnl'] < 0]['pnl'].sum())
        
        if gross_losses > 0:
            return round(gross_profits / gross_losses,4)
        return 0.0

    @staticmethod
    def profit_and_loss_ratio(trade_log:pd.DataFrame):
        """Calculate the ratio of average winning trade to average losing trade."""

        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'pnl' column exists in the DataFrame
        if 'pnl' not in trade_log.columns:
            raise ValueError("'pnl' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0

        # Calculate average win
        avg_win = trade_log[trade_log['pnl'] > 0]['pnl'].mean()
        avg_win = 0 if pd.isna(avg_win) else avg_win
        
        # Calculate average loss
        avg_loss = trade_log[trade_log['pnl'] < 0]['pnl'].mean()
        avg_loss = 0 if pd.isna(avg_loss) else avg_loss

        if avg_loss != 0:
            return round(abs(avg_win / avg_loss),4)
        return 0.0
    
            
    @staticmethod
    def sortino_ratio(trade_log:pd.DataFrame, target_return=0):
        """Calculate the Sortino Ratio for a given trading log."""
        # Check if the input is a pandas DataFrame
        if not isinstance(trade_log, pd.DataFrame):
            raise TypeError("trade_log must be a pandas DataFrame")
        
        # Check if the 'gain/loss' column exists in the DataFrame
        if 'gain/loss' not in trade_log.columns:
            raise ValueError("'gain/loss' column is missing in trade_log DataFrame")
        
        # Check for empty DataFrame
        if trade_log.empty:
            return 0
        
        negative_returns = trade_log[trade_log['gain/loss'] < target_return]['gain/loss']
        expected_return = trade_log['gain/loss'].mean() - target_return
        downside_deviation = negative_returns.std(ddof=1)
        
        if downside_deviation > 0:
            return round(expected_return / downside_deviation,4)
        return 0.0
    
    # -- Comparables -- 
    @staticmethod
    def sharpe_ratio(equity_curve:np.ndarray, risk_free_rate=0.04):
        if not isinstance(equity_curve, np.ndarray):
            raise TypeError("equity_curve must be a numpy array")
        
        # Check for empty array
        if len(equity_curve) == 0:
            return np.array([0])
        else:
            daily_returns = PerformanceStatistics.period_return(equity_curve)
            excess_returns = np.array(daily_returns) - risk_free_rate / 252  # Assuming daily returns, adjust risk-free rate accordingly
            return np.around(np.mean(excess_returns) / np.std(excess_returns, ddof=1),decimals=4) if np.std(excess_returns, ddof=1) != 0 else 0

    # @staticmethod
    # def beta(portfolio_equity_curve: np.ndarray, benchmark_equity_curve: np.ndarray) -> float:
    #     """Calculates the beta of the portfolio based on equity curves."""

    #     if not isinstance(portfolio_equity_curve, np.ndarray):
    #         raise TypeError("portfolio_equity_curve must be a numpy array")
        
    #     if not isinstance(benchmark_equity_curve, np.ndarray):
    #         raise TypeError("benchmark_equity_curve must be a numpy array")
        
    #     # Check for empty array
    #     if len(portfolio_equity_curve) == 0 or len(benchmark_equity_curve) ==0:
    #         return np.array([0])
        
    #     portfolio_returns = PerformanceStatistics.daily_return(portfolio_equity_curve)
    #     benchmark_returns = PerformanceStatistics.daily_return(benchmark_equity_curve)
        
    #     covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
    #     variance = np.var(benchmark_returns, ddof=1)  # Using sample variance
    #     beta_value = covariance / variance
    #     return round(beta_value,4)

    # @staticmethod
    # def alpha(portfolio_equity_curve: np.ndarray, benchmark_equity_curve: np.ndarray, risk_free_rate: float) -> float:
    #     """Calculates the alpha of the portfolio based on equity curves."""

    #     if not isinstance(portfolio_equity_curve, np.ndarray):
    #         raise TypeError("portfolio_equity_curve must be a numpy array")
        
    #     if not isinstance(benchmark_equity_curve, np.ndarray):
    #         raise TypeError("benchmark_equity_curve must be a numpy array")
        
    #     if not isinstance(risk_free_rate, (float, int)):
    #         raise TypeError("risk_free_rate must be a float or int.")
        
    #     # Check for empty array
    #     if len(portfolio_equity_curve) == 0 or len(benchmark_equity_curve) ==0:
    #         return np.array([0])
        
    #     portfolio_returns = PerformanceStatistics.daily_return(portfolio_equity_curve)
    #     benchmark_returns = PerformanceStatistics.daily_return(benchmark_equity_curve)

    #     # Annualize the daily returns
    #     annualized_portfolio_return = np.mean(portfolio_returns) * 252
    #     annualized_benchmark_return = np.mean(benchmark_returns) * 252

    #     # Calculate beta using annualized returns
    #     beta_value = PerformanceStatistics.beta(portfolio_equity_curve, benchmark_equity_curve)

    #     # Calculate alpha using annualized returns and annual risk-free rate
    #     alpha_value = annualized_portfolio_return - (risk_free_rate + beta_value * (annualized_benchmark_return - risk_free_rate))
    #     return round(alpha_value, 4)
    
    # -- Plots --
    @staticmethod
    def plot_curve(y, title='Title', x_label="Time", y_label="Curve", show_plot=True):
        plt.figure(figsize=(12, 6))
        plt.plot(y, label=y_label)
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.axhline(y=0, color='gray', linestyle='--')
        plt.grid()
        plt.legend()

        if show_plot:
            plt.show()

    @staticmethod
    def plot_data_with_signals(data, signals, show_plot=True):
        plt.figure(figsize=(15, 7))

        for symbol in data.columns:
            plt.plot(data.index, data[symbol], label=symbol)

        for signal in signals:
            color = 'green' if signal['direction'] == 1 else 'red'
            plt.scatter(signal['timestamp'], signal['price'], color=color, marker='o' if signal['direction'] == 1 else 'x')

        plt.legend()
        plt.title("Price Data with Trade Signals")
        plt.xlabel("Timestamp")
        plt.ylabel("Price")

        if show_plot:
            plt.show()

    @staticmethod
    def plot_price_and_spread(price_data:pd.DataFrame, spread:list, signals: list, split_date=None, show_plot=True):
        """
        Plot multiple ticker data on the left y-axis and spread with mean and standard deviations on the right y-axis.
        
        Parameters:
            price_data (pd.DataFrame): DataFrame containing the data with timestamps as index and multiple ticker columns.
            spread (pd.Series): Series containing the spread data.
        """
        # Extract data from the DataFrame
        timestamps = price_data.index
        spread = pd.Series(spread, index=timestamps) 

        # Create a figure and primary axis for price data (left y-axis)
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Plot each ticker on the left y-axis
        colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black', 'orange']  # Extend this list as needed
        for i, ticker in enumerate(price_data.columns):
            color = colors[i % len(colors)]  # Cycle through colors
            ax1.plot(timestamps, price_data[ticker], label=ticker, color=color, linewidth=2)

        ax1.set_yscale('linear')
        ax1.set_ylabel('Price')
        ax1.legend(loc='upper left')

        # Calculate mean and standard deviations for spread
        spread_mean = spread.rolling(window=20).mean()  # Adjust the window size as needed
        spread_std_1 = spread.rolling(window=20).std()  # 1 standard deviation
        spread_std_2 = 2 * spread.rolling(window=20).std()  # 2 standard deviations

        # Create a secondary axis for the spread with mean and standard deviations (right y-axis)
        ax2 = ax1.twinx()

        # Plot Spread on the right y-axis
        ax2.plot(timestamps, spread, label='Spread', color='purple', linewidth=2)
        ax2.plot(timestamps, spread_mean, label='Mean', color='orange', linestyle='--')
        ax2.fill_between(timestamps, spread_mean - spread_std_1, spread_mean + spread_std_1, color='gray', alpha=0.2, label='1 Std Dev')
        ax2.fill_between(timestamps, spread_mean - spread_std_2, spread_mean + spread_std_2, color='gray', alpha=0.4, label='2 Std Dev')
        ax2.set_yscale('linear')
        ax2.set_ylabel('Spread and Statistics')
        ax2.legend(loc='upper right')


        # Plot signals
        for signal in signals:
            ts = pd.to_datetime(signal['timestamp'])
            price = signal['price']
            action = signal['action']
            if action in ['LONG', 'COVER']:
                marker = '^'
                color = 'lime'
            elif action in ['SHORT', 'SELL']:
                marker = 'v'
                color = 'red'
            else:
                # Default marker for undefined actions
                marker = 'o'
                color = 'gray'
            ax1.scatter(ts, price, marker=marker, color=color, s=100)

        # Draw a dashed vertical line to separate test and training data
        if split_date is not None:
            split_date = pd.to_datetime(split_date)
            ax1.axvline(x=split_date, color='black', linestyle='--', linewidth=1)

        # Add grid lines
        ax1.grid(True)

        # Format x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.xlabel('Timestamp')

        # Title
        plt.title('Price Data, Spread, and Statistics Over Time')

        # Show the plot
        plt.tight_layout()

        if show_plot:
            plt.show()

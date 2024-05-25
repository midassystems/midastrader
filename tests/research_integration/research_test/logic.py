import numpy as np
import pandas as pd
from typing import Dict
from enum import Enum, auto
from fractions import Fraction

from midas.research.data import DataProcessing
from midas.research.strategy import BaseStrategy
from quantAnalytics.report import ReportGenerator
from quantAnalytics.statistics import TimeseriesTests
from quantAnalytics.visualization import Visualizations

class Signal(Enum):
    """ Long and short are treated as entry actions and short/cover are treated as exit actions. """
    Overvalued = auto()
    Undervalued = auto()
    Exit_Overvalued = auto()
    Exit_Undervalued = auto()

class Cointegrationzscore(BaseStrategy):
    def __init__(self,symbols:list, report:ReportGenerator):
        #report
        self.report=report
        self.symbols=symbols

        # parameters
        self.zscore_lookback_period = 30
        self.entry_threshold = 2
        self.exit_threshold = 1

        # data
        self.historical_data : pd.DataFrame = None
        self.train_data : pd.DataFrame = None
        self.cointegration_vector = None
        # self.hedge_ratio = None
        self.historical_spread = []
        self.historical_zscore = []
        self.last_signal = None 

        # self.signals : pd.DataFrame

    def prepare(self, historical_data:pd.DataFrame) -> None:
        self.report.add_main_title("Cointegration Z-score")

        # Initial data
        self.historical_data = historical_data

        # Train Data
        self.train_data = pd.DataFrame(index=self.historical_data.index)

        for symbol in self.historical_data.columns:
            log_column_name = f"{symbol}_log"  # Creates a new column name for log prices
            self.train_data[log_column_name] = np.log(self.historical_data[symbol])

        # Cointegration Vector 
        cointegration_results = self._cointegration(self.train_data)
        cointegration_vector = cointegration_results['cointegration_vector']

        # Hedge Ratios
        standardized_vector = self._standardize_coint_vector_auto_min(cointegration_vector)
        self.cointegration_vector = self._adjust_hedge_ratios(standardized_vector)
        self.weights = self._asset_allocation(self.symbols, self.cointegration_vector) # Create hedge ratio dictionary

        # Create Spread
        self.historical_spread = self._historic_spread(self.train_data, self.cointegration_vector)
        self.historical_data['spread'] = self.historical_spread
        
        # Create Z-Score
        self.historical_zscore = self._historic_zscore(self.zscore_lookback_period)
        self.historical_data['zscore'] = self.historical_zscore

        # Validation tests on spread/z-score data
        validation_results = self._data_validation()

        # Cointegration vector data
        cointegration_df = pd.DataFrame({
            "cointegration vector": cointegration_vector,
            "standardized vector": standardized_vector,
            "hedge ratios": self.cointegration_vector
        })
        cointegration_df=cointegration_df.T
        cointegration_df.columns=self.symbols       
        
        # Spread data
        spread_stats = pd.DataFrame({
            "Half-life": [validation_results['hurst_exponent']],
            "Hurst Exponent": [validation_results['half_life']]
        })

        # Add preprocessing data to report
        self.report.add_text("<section class='preprocessing'>")
        self.report.add_section_title("Preprocessing")
        self.report.add_text(TimeseriesTests.display_johansen_results(cointegration_results['johansen_results'], cointegration_results['num_cointegrations'],cointegration_results['lag'], False, True, indent = 1))
        self.report.add_text(TimeseriesTests.display_adf_results({'spread': validation_results['adf_test']}, False, True, indent = 1))
        self.report.add_text(TimeseriesTests.display_pp_results({'spread': validation_results['pp_test']}, False, True, indent = 1))
        self.report.add_dataframe(cointegration_df, "Cointegration Vector")
        self.report.add_dataframe(spread_stats, "Spread Statistics", index=False)
        self.report.add_image(Visualizations.line_plot, indent = 1, y = self.historical_spread, x = pd.to_datetime(self.historical_data.index, unit='ns'), title = "Historical Spread", x_label="Time", y_label="Spread")
        self.report.add_image(Visualizations.line_plot, indent = 1, y = self.historical_zscore, x = pd.to_datetime(self.historical_data.index, unit='ns'), title = "Historical Z-Score", x_label="Time", y_label="Z-Score")
        self.report.add_text("</section>")

    def _cointegration(self, train_data:pd.DataFrame) -> None:
        # Determine Lag Length
        lag = TimeseriesTests.select_lag_length(data=train_data)
        
        # Test Cointegration Relationship
        johansen_results, num_cointegrations = TimeseriesTests.johansen_test(data=train_data, k_ar_diff=lag-1)
        cointegration_vector = johansen_results['Cointegrating Vector'][0]

        results = {
            'lag': lag,
            'num_cointegrations': num_cointegrations,
            'johansen_results': johansen_results,
            'cointegration_vector': cointegration_vector
        }
    
        return results
    
    def _standardize_coint_vector_auto_min(self, coint_vector:list) -> np.ndarray:
        """
        Standardizes a cointegration vector so that the component with the smallest absolute value is 1.
        
        Parameters:
        - coint_vector (list or numpy array): The cointegration vector.
        
        Returns:
        - numpy array: A new cointegration vector where the component with the smallest absolute value is 1.
        """
        # Convert to numpy array for easier calculations
        coint_vector = np.array(coint_vector)
        
        # Find the index of the component with the smallest absolute value
        standard_index = np.argmin(np.abs(coint_vector))
        
        # Scale the vector so that the component at standard_index is 1
        standard_value = coint_vector[standard_index]
        standardized_vector = coint_vector / standard_value
        
        return standardized_vector

    def _adjust_hedge_ratios(self, hedge_ratios:np.ndarray) -> np.ndarray:
        """
        Adjusts hedge ratios to whole numbers by rounding or scaling.
        
        Parameters:
        - hedge_ratios (numpy array): The hedge ratios, typically normalized cointegration vector.
        
        Returns:
        - numpy array: Adjusted hedge ratios where all values are whole numbers.
        """
        # Attempt to round the hedge ratios to the nearest whole number
        rounded_ratios = np.round(hedge_ratios * 2) / 2

        # Find the least common multiple (LCM) of the denominators of the fractions to scale them up to whole numbers
        denominators = [frac.denominator for frac in np.vectorize(Fraction)(rounded_ratios)]
        lcm = np.lcm.reduce(denominators)
        
        # Scale the ratios up to whole numbers
        whole_number_ratios = rounded_ratios * lcm

        return whole_number_ratios

    def _asset_allocation(self, symbols:list, cointegration_vector:np.array) -> dict:
        if len(cointegration_vector) != len(symbols):
            raise ValueError("Length of cointegration vector must match the number of symbols.")

        # Create a dictionary of symbols and corresponding hedge ratios
        return {symbol: ratio for symbol, ratio in zip(symbols, cointegration_vector)}
    
    def _historic_spread(self, train_data:pd.DataFrame, cointegration_vector:np.array) -> list:
        new_spread = train_data.dot(cointegration_vector) # produces a pd.Series
        historical_spread = new_spread.tolist()
        return historical_spread

    def _historic_zscore(self, lookback_period:int) -> np.ndarray:
        # Convert historical spread to a pandas Series for convenience
        spread_series = pd.Series(self.historical_spread)
        
        if lookback_period is not None:
            # Use a rolling window if lookback_period is specified
            mean = spread_series.rolling(window=lookback_period).mean()
            std = spread_series.rolling(window=lookback_period).std()
        else:
            # Use an expanding window if lookback_period is None, considering all data up to each point
            mean = spread_series.expanding().mean()
            std = spread_series.expanding().std()
        
        # Calculate z-score
        historical_zscore = ((spread_series - mean) / std).to_numpy()

        return historical_zscore

    def _data_validation(self) -> dict:
        results = {
            'adf_test': TimeseriesTests.adf_test(self.historical_spread),
            'pp_test': TimeseriesTests.phillips_perron_test(self.historical_spread),
            'hurst_exponent': TimeseriesTests.hurst_exponent(self.historical_spread),
            'half_life': None, 
        }
        
        # Calculate half-life and add to results
        results['half_life'], _ = TimeseriesTests.half_life(pd.Series(self.historical_spread))
        
        return results
      
    # -- Strategy logic -- 
    def _update_spread(self, train_data:pd.DataFrame, cointegration_vector:np.array) -> list:
        new_spread = train_data.dot(cointegration_vector) # produces a pd.Series
        historical_spread = new_spread.tolist()
        return historical_spread
    
    def _update_zscore(self, spread:list, lookback_period:int) -> np.ndarray:
        """
        Update z-scores using new spread data, extending from a historical spread with a given lookback period.

        Parameters:
        - spread (list): New spread data to be added.
        - lookback_period (int): Number of periods used for lookback in z-score calculation.

        Returns:
        - np.ndarray: Array of updated z-scores corresponding to the new data.
        """
        # Convert historical spread to a pandas Series for convenience
        old_spread_series = pd.Series(self.historical_spread)
        new_spread_series = pd.Series(spread)

        # Concatenate recent historical data with new spread data
        if lookback_period is not None:
            recent_spread = old_spread_series[-lookback_period:]
            spread_series = pd.concat([recent_spread, new_spread_series], ignore_index=True)
        else:
            spread_series = pd.concat([old_spread_series, new_spread_series], ignore_index=True)

        # Calculate rolling mean and standard deviation based on the lookback period
        mean = spread_series.rolling(window=lookback_period).mean()
        std = spread_series.rolling(window=lookback_period).std()

        # Calculate z-scores, only for the new spread portion
        z_scores = (spread_series - mean) / std

        # Return only the z-scores for the new data
        return z_scores[-len(new_spread_series):].to_numpy()

    def _entry_signal(self, z_score:float, entry_threshold:float) -> bool:
        """
        Entry logic.

        Parameters: 
        - z_score (float): Current value of the z-score.
        - entry_threshold (float): Absolute value of z-score that triggers an entry signal.

        Returns:
        - bool : True if an entry signal else False.
        """
        if self.last_signal == None and z_score >= entry_threshold:
            self.last_signal = Signal.Overvalued
            return True
        elif self.last_signal == None and z_score <= -entry_threshold:
            self.last_signal = Signal.Undervalued
            return True
        else:
            return False
    
    def _exit_signal(self, z_score:float, exit_threshold:float) -> bool:
        """ 
        Exit logic.

        Parameters: 
        - z_score (float): Current value of the z-score.
        - exit_threshold (float): Absolute value of z-score that triggers an exit signal.

        Returns:
        - bool : True if an exit signal else False.
        """
        if self.last_signal == Signal.Undervalued and z_score >= exit_threshold:
            self.last_signal = Signal.Exit_Undervalued
            return True
        elif self.last_signal == Signal.Overvalued and z_score <= -exit_threshold:
                self.last_signal = Signal.Exit_Overvalued
                return True
        else: 
            return False

    def generate_signals(self, test_data:pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals in backtest. LONG = 1, SHORT = -1, NO SIGNAL = 0

        Parameters:
        - entry_threshold: The threshold to trigger a trade entry.
        - exit_threshold: The threshold to trigger a trade exit.
        - lag (int): The number of periods the entry/exit of a position will be lagged after a signal.

        Returns:
        - pandas.DataFrame : Contains the results of the backtests, including original data plus signals and positions.
        """
        # Initialize an empty DataFrame for signals with the same index as historical data
        self.signals = pd.DataFrame(index=test_data.index)

        # Log price data
        log_test_data = pd.DataFrame(index=test_data.index)
        for symbol in test_data.columns:
            log_column_name = f"{symbol}_log"  # Creates a new column name for log prices
            log_test_data[log_column_name] = np.log(test_data[symbol])
        
        # Creat spread for test data
        test_spread = self._update_spread(log_test_data, self.cointegration_vector)
        test_data['spread'] = test_spread
        
        # Create Z-Score for test data
        test_zscore = self._update_zscore(test_spread, self.zscore_lookback_period)
        test_data['zscore'] = test_zscore

        # Initialize signals with zeros
        for ticker in self.weights:
            self.signals[f'{ticker}'] = np.nan

        # Iterate through DataFrame rows
        for i in range(1, len(test_data)):
            current_zscore = test_data.iloc[i]['zscore']

            # Continue to next iteration if current Z-score is NaN
            if np.isnan(current_zscore):
                continue

            # Check for entry signals
            if self._entry_signal(current_zscore, self.entry_threshold):
                for ticker, weights in self.weights.items():
                    if self.last_signal == Signal.Undervalued and weights > 0:
                        self.signals.at[self.signals.index[i], f'{ticker}'] = 1
                    elif self.last_signal == Signal.Undervalued and weights < 0:
                        self.signals.at[self.signals.index[i], f'{ticker}'] = -1
                    elif self.last_signal == Signal.Overvalued and weights > 0:
                        self.signals.at[self.signals.index[i], f'{ticker}'] = -1
                    elif self.last_signal == Signal.Overvalued and weights < 0:
                        self.signals.at[self.signals.index[i], f'{ticker}'] = 1

            # Check for exit signals        
            elif self._exit_signal(current_zscore, self.exit_threshold):
                for ticker in self.weights.keys():
                    self.signals.loc[self.signals.index[i], f'{ticker}'] = 0
                self.last_signal = None # reset to no position

        return self.signals


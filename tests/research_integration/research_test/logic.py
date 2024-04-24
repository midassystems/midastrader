import numpy as np
import pandas as pd
from typing import Dict
from enum import Enum, auto

from research.strategy import BaseStrategy
from research.data import DataProcessing
from research.analysis import TimeseriesTests

class Signal(Enum):
    """ Long and short are treated as entry actions and short/cover are treated as exit actions. """
    Overvalued = auto()
    Undervalued = auto()
    Exit_Overvalued = auto()
    Exit_Undervalued = auto()

class Cointegrationzscore(BaseStrategy):
    def __init__(self):
        self.last_signal = None  # 0: no position, 1: long, -1: short
        self.zscore_lookback=30
        self.historical_data = None
        self.cointegration_vector = None
        self.historical_spread = []
        self.historical_zscore = []

    def prepare(self, train_data: pd.DataFrame) -> str:
        # Convert Unix to ISO
        # train_data.index = pd.to_datetime(train_data.index, unit='s')
        symbols = train_data.columns.tolist()

        # train_data = adjust_to_business_time(train_data, frequency='daily')
        self.historical_data = train_data
        cointegration_results = self._cointegration(train_data) # Run cointegration test
        self.cointegration_vector = cointegration_results['cointegration_vector']

        tab = "    "
        html_content = "<section class='analysis'>\n"
        html_content += f"{tab}<p>Ideal Lag : {cointegration_results['lag']}</p>\n"
        html_content +=  f"{TimeseriesTests.display_johansen_results(cointegration_results['johansen_results'], cointegration_results['num_cointegrations'], False, True, indent = 1)}\n"
        html_content += f"{tab}<p>Cointegration Vector : {cointegration_results['cointegration_vector']}</p>\n"

        self._historic_spread(train_data, self.cointegration_vector)
        self.historical_data['spread'] = self.historical_spread
        
        self._historic_zscore()
        self.historical_data['zscore'] = self.historical_zscore

        # Create hedge ratio dictionary
        self._asset_allocation(symbols, self.cointegration_vector)
        

        # Validate the spread/z-score data
        validation_results = self._data_validation()

        html_content += f"{TimeseriesTests.display_adf_results({'spread': validation_results['adf_test']}, False, True, indent = 1)}\n"
        html_content += f"{TimeseriesTests.display_pp_results({'spread': validation_results['pp_test']}, False, True, indent = 1)}\n"
        # html_content += f"{tab}<p>Hurst Exponent: {validation_results['hurst_exponent']}</p>\n"
        html_content += f"{tab}<p>Half-Life: {validation_results['half_life']}</p>\n"
        html_content += "</section>"

        return html_content

    def _cointegration(self, train_data:pd.DataFrame) -> None:
        # Determine Lag Length
        lag = TimeseriesTests.select_lag_length(data=train_data)
        # lag = 2 # delete
        
        # Check Cointegration Relationship
        johansen_results, num_cointegrations = TimeseriesTests.johansen_test(data=train_data, k_ar_diff=lag-1)
        
        #Create Cointegration Vector
        cointegration_vector = johansen_results['Cointegrating Vector'][0] # TODO: check type

        results = {
            'lag': lag,
            'num_cointegrations': num_cointegrations,
            'johansen_results': johansen_results,
            'cointegration_vector': cointegration_vector
        }
    
        return results

    def _historic_spread(self, train_data: pd.DataFrame, cointegration_vector: np.array) -> None:
        new_spread = train_data.dot(cointegration_vector) # produces a pd.Series
        self.historical_spread = new_spread.tolist()

    def _historic_zscore(self) -> None:
        # Convert historical spread to a pandas Series for convenience
        spread_series = pd.Series(self.historical_spread)
        
        if self.zscore_lookback is not None:
            # Use a rolling window if lookback_period is specified
            mean = spread_series.rolling(window=self.zscore_lookback).mean()
            std = spread_series.rolling(window=self.zscore_lookback).std()
        else:
            # Use an expanding window if lookback_period is None, considering all data up to each point
            mean = spread_series.expanding().mean()
            std = spread_series.expanding().std()
        
        # Calculate z-score
        self.historical_zscore = ((spread_series - mean) / std).to_numpy()

    def _data_validation(self) -> dict:
        results = {
            'adf_test': TimeseriesTests.adf_test(self.historical_spread),
            'pp_test': TimeseriesTests.phillips_perron_test(self.historical_spread),
            # 'hurst_exponent': TimeseriesTests.hurst_exponent(self.historical_spread),
            'half_life': None,  # This will be calculated and added below
        }
        
        # Prepare data for half-life calculation
        spread_series = pd.Series(self.historical_spread)
        spread_lagged = TimeseriesTests.lag_series(spread_series)
        spread_combined = pd.DataFrame({'Original': spread_series, 'Lagged': spread_lagged}).dropna()
        
        # Calculate half-life and add to results
        half_life, residuals = TimeseriesTests.half_life(Y=spread_combined['Original'], Y_lagged=spread_combined['Lagged'])
        results['half_life'] = half_life
        
        return results

    def _asset_allocation(self, symbols: list, cointegration_vector: np.array) -> None:
        self.cointegration_vector_dict = {symbol: ratio for symbol, ratio in zip(symbols, cointegration_vector)}

        # Normalize the cointegration vector
        normalized_cointegration_vector = cointegration_vector / np.sum(np.abs(cointegration_vector))

        # Ensure the length of the normalized cointegration vector matches the number of symbols
        if len(normalized_cointegration_vector) != len(symbols):
            raise ValueError("Length of normalized cointegration vector must match the number of symbols.")

        # Create a dictionary of symbols and corresponding normalized hedge ratios
        self.hedge_ratio = {symbol: ratio for symbol, ratio in zip(symbols, normalized_cointegration_vector)}
      
    def _entry_signal(self, z_score: float, entry_threshold: float) -> bool:
        # Entry logic
        if self.last_signal == None and z_score >= entry_threshold:
            self.last_signal = Signal.Overvalued
            return True
        elif self.last_signal == None and z_score <= -entry_threshold:
            self.last_signal = Signal.Undervalued
            return True
        else:
            return False
    
    def _exit_signal(self, z_score: float, exit_threshold: float) -> bool:
        # Exit logic
        if self.last_signal == Signal.Undervalued and z_score >= exit_threshold:
            self.last_signal = Signal.Exit_Undervalued
            return True
        elif self.last_signal == Signal.Overvalued and z_score <= -exit_threshold:
                self.last_signal = Signal.Exit_Overvalued
                return True
        else: 
            return False

    def generate_signals(self, entry_threshold:float=2, exit_threshold:float=0, lag:int=1) -> pd.DataFrame:
        # Initialize signals with zeros
        for ticker in self.hedge_ratio:
            self.historical_data[f'{ticker}_signal'] = np.nan

        # Iterate through DataFrame rows
        for i in range(1, len(self.historical_data)):
            current_zscore = self.historical_data.iloc[i]['zscore']

            if np.isnan(current_zscore):
                continue

            if self._entry_signal(current_zscore, entry_threshold):
                for ticker, hedge_ratio in self.hedge_ratio.items():
                    if self.last_signal == Signal.Undervalued and hedge_ratio > 0:
                        self.historical_data.loc[self.historical_data.index[i], f'{ticker}_signal'] = 1
                    elif self.last_signal == Signal.Undervalued and hedge_ratio < 0:
                        self.historical_data.loc[self.historical_data.index[i], f'{ticker}_signal'] = -1
                    elif self.last_signal == Signal.Overvalued and hedge_ratio > 0:
                        self.historical_data.loc[self.historical_data.index[i], f'{ticker}_signal'] = -1
                    elif self.last_signal == Signal.Overvalued and hedge_ratio < 0:
                        self.historical_data.loc[self.historical_data.index[i], f'{ticker}_signal'] = 1
            elif self._exit_signal(current_zscore, exit_threshold):
                for ticker in self.hedge_ratio.keys():
                    self.historical_data.loc[self.historical_data.index[i], f'{ticker}_signal'] = 0
                self.last_signal = None # reset to no position

        self.calculate_positions(lag)
        return self.historical_data

    def calculate_positions(self, lag:int=1) -> None:
        # Assuming 'hedge_ratios' contains the tickers as keys
        hedge_ratios = self.hedge_ratio
        
        for ticker in hedge_ratios.keys():
            signal_column = f'{ticker}_signal'
            position_column = f'{ticker}_position'
            
            self.historical_data[position_column] = self.historical_data[signal_column]
            self.historical_data[position_column] = self.historical_data[position_column].ffill()
            self.historical_data[position_column].shift(lag)
            self.historical_data[position_column] = self.historical_data[position_column].fillna(0)

    def handle_market_data(self):
        """ Process market data and generate trading signals. """
        pass
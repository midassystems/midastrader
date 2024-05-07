import logging
import numpy as np
import pandas as pd
from queue import Queue
from typing import Dict
from decimal import Decimal
from enum import Enum, auto

from midas.engine.order_book import OrderBook
from midas.engine.strategies import BaseStrategy
from midas.engine.portfolio import PortfolioServer

from midas.shared.symbol import Symbol
from midas.shared.signal import TradeInstruction
from midas.shared.orders import OrderType, Action
from midas.shared.analysis import TimeseriesTests


def convert_decimals_to_floats(df: pd.DataFrame):
    for column in df.columns:
        if df[column].dtype == object and isinstance(df[column].iloc[0], Decimal):
            df[column] = df[column].apply(float)  # Convert Decimal to float
    return df

class Signal(Enum):
    """ Long and short are treated as entry actions and short/cover are treated as exit actions. """
    Overvalued = auto()
    Undervalued = auto()
    Exit_Overvalued = auto()
    Exit_Undervalued = auto()

class Cointegrationzscore(BaseStrategy):
    def __init__(self, symbols_map:Dict[str, Symbol], train_data:pd.DataFrame, portfolio_server: PortfolioServer, logger:logging.Logger, order_book:OrderBook,event_queue:Queue):
        super().__init__(portfolio_server,order_book, logger, event_queue)
        self.symbols_map = symbols_map
        self.trade_id = 1
        
        self.historical_data = None
        self.cointegration_vector = None
        self.historical_spread = []
        self.historical_zscore = []

        self.last_signal = None  # 0: no position, 1: long, -1: short
        self.current_zscore = None
        self.cointegration_vector_dict = {}
        self.hedge_ratio = {}

        self.prepare(train_data)

    def prepare(self, train_data: pd.DataFrame):
        # train_data = adjust_to_business_time(train_data, frequency='daily')
        self.historical_data = convert_decimals_to_floats(train_data)
        self.cointegration_vector = self._cointegration(train_data)

        # Establish histroccal values
        self._historic_spread(train_data, self.cointegration_vector)
        self._historic_zscore()
        
        # Create hedge ratio dictionary
        symbols = train_data.columns.tolist()
        self._asset_allocation(symbols, self.cointegration_vector)
        
        self._data_validation()

    def _cointegration(self, train_data: pd.DataFrame):
        print(train_data)
        # Determine Lag Length
        # lag = TimeseriesTests.select_lag_length(data=train_data)
        lag =2
        
        # Check Cointegration Relationship
        johansen_results, num_cointegrations = TimeseriesTests.johansen_test(data=train_data, k_ar_diff=lag-1)
        
        #Create Cointegration Vector
        cointegration_vector = johansen_results['Cointegrating Vector'][0]

        # Log Results
        self.logger.info(f"Ideal Lag : {lag}")
        self.logger.info(TimeseriesTests.display_johansen_results(johansen_results, num_cointegrations, False))
        self.logger.info(f"Cointegration Vector :{cointegration_vector}")

        return cointegration_vector

    def _historic_spread(self, train_data: pd.DataFrame, cointegration_vector: np.array) -> None:
        new_spread = train_data.dot(cointegration_vector) # produces a pd.Series
        self.historical_spread = new_spread.tolist()

    def _historic_zscore(self, lookback_period=30) -> None:
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
        
        # Calculate z-score and convert to a list
        self.historical_zscore = ((spread_series - mean) / std).dropna().tolist()

    def _data_validation(self):
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
        # half_life, residuals = TimeseriesTests.half_life(Y=spread_combined['Original'], Y_lagged=spread_combined['Lagged'])
        # results['half_life'] = half_life

        # Log the results 
        self.logger.info(TimeseriesTests.display_adf_results({'spread': results['adf_test']}, False))
        self.logger.info(TimeseriesTests.display_pp_results({'spread': results['pp_test']}, False))
        # self.logger.info(f"\nHurst Exponent: {results['hurst_exponent']}")
        # self.logger.info(f"\nHalf-Life: {results['half_life']}")

    def _update_spread(self, new_data: pd.DataFrame):
        # Convert the cointegration vector dictionary to a pandas Series
        cointegration_series = pd.Series(self.cointegration_vector_dict)

        # Ensure the new_data DataFrame is aligned with the cointegration vector
        aligned_new_data = new_data[cointegration_series.index]

        # Calculate the new spread value
        new_spread_value = aligned_new_data.dot(cointegration_series)
        
        # Append the new spread value to the historical spread list
        self.historical_spread.append(new_spread_value.item())
    
    def _update_zscore(self,lookback_period=None):
        # Determine the lookback range for the z-score calculation
        spread_lookback = self.historical_spread[-lookback_period:] if lookback_period else self.historical_spread

        # Calculate and append the new z-score
        self.current_zscore = self._calculate_single_zscore(spread_lookback)
        self.logger.info(f"Current z-score {self.current_zscore}")
        self.historical_zscore.append(self.current_zscore)

    def _calculate_single_zscore(self, spread_lookback):
        if len(spread_lookback) < 2:
            return 0
        mean = np.mean(spread_lookback)
        std = np.std(spread_lookback)
        return (spread_lookback[-1] - mean) / std if std != 0 else 0
    
    def _asset_allocation(self, symbols: list, cointegration_vector: np.array):
        """
        Create a dictionary of hedge ratios for each ticker.

        Parameters:
            symbols (list): List of ticker symbols.
            cointegration_vector (np.array): Array representing the cointegration vector (hedge ratios).

        Returns:
            dict: Dictionary with tickers as keys and hedge ratios as values.
        """

        self.cointegration_vector_dict = {symbol: ratio for symbol, ratio in zip(symbols, cointegration_vector)}

        # Normalize the cointegration vector
        normalized_cointegration_vector = cointegration_vector / np.sum(np.abs(cointegration_vector))

        # Ensure the length of the normalized cointegration vector matches the number of symbols
        if len(normalized_cointegration_vector) != len(symbols):
            raise ValueError("Length of normalized cointegration vector must match the number of symbols.")

        # Create a dictionary of symbols and corresponding normalized hedge ratios
        self.hedge_ratio = {symbol: ratio for symbol, ratio in zip(symbols, normalized_cointegration_vector)}
        self.logger.info(self.hedge_ratio)

    def _entry_signal(self, z_score: float, entry_threshold: float):
        if not any(ticker in self.portfolio_server.positions for ticker in self.symbols_map.keys()):
            if z_score > entry_threshold: # overvalued
                self.last_signal = Signal.Overvalued
                self.logger.info(f"Entry signal z_score : {z_score} // entry_threshold : {entry_threshold} // action : {self.last_signal}")
                return True
            elif z_score < -entry_threshold:
                self.last_signal = Signal.Undervalued
                self.logger.info(f"Entry signal z_score : {z_score} // entry_threshold : {entry_threshold} // action : {self.last_signal}")
                return True
        else:
            return False

    def _exit_signal(self, z_score: float, exit_threshold: float):
        if any(ticker in self.portfolio_server.positions for ticker in self.symbols_map.keys()):
            if self.last_signal == Signal.Undervalued and z_score >= exit_threshold:
                self.last_signal = Signal.Exit_Undervalued
                self.logger.info(f"Exit signal z_score : {z_score} // entry_threshold : {exit_threshold} // action : {self.last_signal}")
                return True
            elif self.last_signal == Signal.Overvalued and z_score <= -exit_threshold:
                self.last_signal = Signal.Exit_Overvalued
                self.logger.info(f"Exit signal z_score : {z_score} // entry_threshold : {exit_threshold} // action : {self.last_signal}")
                return True
        else: 
            return False
    
    def generate_trade_instructions(self, signal: Signal):
        trade_instructions = []
        leg_id = 1

        for ticker, hedge_ratio in self.hedge_ratio.items():
            if signal in [Signal.Overvalued, Signal.Exit_Undervalued]:
                if hedge_ratio < 0:
                    action = Action.LONG if signal == Signal.Overvalued else Action.COVER
                    hedge_ratio *= -1
                elif hedge_ratio > 0:
                    action = Action.SHORT if signal == Signal.Overvalued else Action.SELL
                    hedge_ratio *= -1
            elif signal in [Signal.Undervalued, Signal.Exit_Overvalued]:
                if hedge_ratio > 0:
                    action = Action.LONG if signal == Signal.Undervalued else Action.COVER
                elif hedge_ratio < 0:
                    action = Action.SHORT if signal == Signal.Undervalued else Action.SELL
            
            trade_instructions.append(TradeInstruction(ticker=ticker, 
                                                       order_type=OrderType.MARKET, 
                                                       action=action,
                                                       trade_id= self.trade_id, 
                                                       leg_id=leg_id, 
                                                       weight=hedge_ratio))
            leg_id += 1
            
        return trade_instructions 
    
    def trade_capital(self, trade_allocation: float=0.5):
        trade_capital = self.portfolio_server.capital * trade_allocation
        self.logger.info(f"Trade Capital: {trade_capital}")
        return trade_capital
    
    def handle_market_data(self, data= None, entry_threshold: float=0.5, exit_threshold: float=0.0):
        trade_instructions = None
        # Get current_prices from order_book
        close_values = self.order_book.current_prices()
        data = pd.DataFrame([close_values])

        # Update features
        self._update_spread(data)
        self._update_zscore()

        if self._exit_signal(self.current_zscore, exit_threshold):
            trade_instructions = self.generate_trade_instructions(self.last_signal) 
            self.trade_id += 1
            self.last_signal = None
        elif self._entry_signal(self.current_zscore, entry_threshold):
            trade_instructions = self.generate_trade_instructions(self.last_signal)
        
        if trade_instructions:
            trade_capital = self.trade_capital()
            self.set_signal(trade_instructions, trade_capital,self.order_book.last_updated)
    
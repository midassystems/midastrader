import math
import logging
import numpy as np
import pandas as pd
from queue import Queue
from decimal import Decimal
from enum import Enum, auto
from typing import Dict, List
from fractions import Fraction

from midas.shared.symbol import Symbol
from midas.engine.order_book import OrderBook
from midas.engine.strategies import BaseStrategy
from midas.engine.portfolio import PortfolioServer
from midas.shared.signal import TradeInstruction, OrderType, Action
from midas.shared.utils import unix_to_iso

from quantAnalytics.statistics import TimeseriesTests


def convert_decimals_to_floats(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        if df[column].dtype == object and isinstance(df[column].iloc[0], Decimal):
            df[column] = df[column].apply(float)  # Convert Decimal to float
    return df


class Signal(Enum):
    """Long and short are treated as entry actions and short/cover are treated as exit actions."""

    Overvalued = auto()
    Undervalued = auto()
    Exit_Overvalued = auto()
    Exit_Undervalued = auto()


class Cointegrationzscore(BaseStrategy):
    def __init__(
        self,
        symbols_map: Dict[str, Symbol],
        historical_data: pd.DataFrame,
        portfolio_server: PortfolioServer,
        logger: logging.Logger,
        order_book: OrderBook,
        event_queue: Queue,
    ):
        print(historical_data)
        # Process data
        historical_data = historical_data.pivot(
            index="timestamp", columns="symbol", values="close"
        )
        historical_data = convert_decimals_to_floats(historical_data)

        # Initialize base
        super().__init__(
            symbols_map,
            historical_data,
            portfolio_server,
            order_book,
            logger,
            event_queue,
        )

        # Parameters
        self.trade_id = 1
        self.zscore_lookback_period = 30
        self.entry_threshold = 2
        self.exit_threshold = 1
        self.trade_allocation = 0.5  # percentage of all cash available

        # Strategy data
        self.train_data: pd.DataFrame
        self.cointegration_vector = None
        self.weights = {}
        self.historical_spread = []
        self.historical_zscore = []
        self.last_signal = None  # 0: no position, 1: long, -1: short
        self.current_zscore = None
        self.hedge_ratio = None
        self.asset_allocation = None

        # set-up
        self.prepare()

    def prepare(self) -> None:
        # Adjust to log
        symbols = self.historical_data.columns.tolist()
        print(symbols)
        print(self.train_data)
        self.train_data = self._log_prices(self.historical_data)

        # Cointegration Vector
        cointegration_vector = self._cointegration(self.train_data)

        # Hedge Ratios
        standardized_vector = self._standardize_coint_vector_auto_min(
            cointegration_vector
        )
        self.cointegration_vector = self._adjust_hedge_ratios(standardized_vector)
        self.hedge_ratio, self.asset_allocation = self._asset_allocation(
            symbols, self.cointegration_vector
        )
        self.logger.info(f"\nHEDGE RATIOS : {self.hedge_ratio}\n")

        # Create Spread
        self.historical_spread = list(
            self._historic_spread(self.train_data, self.cointegration_vector)
        )

        # Create Z-Score
        self.historical_zscore = list(
            self._historic_zscore(self.zscore_lookback_period)
        )

        # Validation tests on spread/z-score data
        self._data_validation()

    def _log_prices(self, df: pd.DataFrame) -> pd.DataFrame:
        # Set new log_df to match df.index
        log_df = pd.DataFrame(index=df.index)

        # Log each column
        for symbol in df.columns:
            log_df[symbol] = np.log(df[symbol])

        return log_df

    def _cointegration(self, train_data: pd.DataFrame) -> list:
        """
        Determines the cointegration relationship between the assets in the data passed using the Johansen cointegration test.

        Parameters:
        - train_data (pd.DataFrame) : Data to be used in training the cointegration relationship.

        Returns:
        - list : Cointegration vector.
        """
        # Determine Lag Length
        lag = TimeseriesTests.select_lag_length(data=train_data)

        # Check Cointegration Relationship
        johansen_results, num_cointegrations = TimeseriesTests.johansen_test(
            data=train_data, k_ar_diff=lag - 1
        )

        # Create Cointegration Vector
        cointegration_vector = johansen_results["Cointegrating Vector"][0]

        # Log Results
        self.logger.info(
            f"{TimeseriesTests.display_johansen_results(johansen_results, num_cointegrations, lag, False)}\n"
        )

        return cointegration_vector

    def _standardize_coint_vector_auto_min(self, coint_vector: list) -> np.ndarray:
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

    def _adjust_hedge_ratios(self, hedge_ratios: np.ndarray) -> np.ndarray:
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
        denominators = [
            frac.denominator for frac in np.vectorize(Fraction)(rounded_ratios)
        ]
        lcm = np.lcm.reduce(denominators)

        # Scale the ratios up to whole numbers
        whole_number_ratios = rounded_ratios * lcm

        return whole_number_ratios

    def _asset_allocation(
        self, symbols: list, cointegration_vector: np.ndarray
    ) -> tuple[dict, dict]:
        """
        Create a dictionary of hedge ratios for each ticker.

        Parameters:
        - symbols (list): List of ticker symbols.
        - cointegration_vector (np.array): Array representing the cointegration vector (hedge ratios).

        Returns:
        - dict: Dictionary with tickers as keys and hedge ratios as values.
        """
        if len(cointegration_vector) != len(symbols):
            raise ValueError(
                "Length of cointegration vector must match the number of symbols."
            )

        # Create a dictionary of symbols and corresponding hedge ratios
        asset_allocation = {}
        hedge_ratios = {}
        for symbol, ratio in zip(symbols, cointegration_vector):
            asset_allocation[symbol] = abs(ratio / abs(cointegration_vector).sum())
            hedge_ratios[symbol] = ratio

        return hedge_ratios, asset_allocation

    def _historic_spread(
        self, train_data: pd.DataFrame, cointegration_vector: np.array
    ) -> list:
        new_spread = train_data.dot(cointegration_vector)  # produces a pd.Series
        historical_spread = new_spread.tolist()
        return historical_spread

    def _historic_zscore(self, lookback_period: int) -> np.ndarray:
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

    def _data_validation(self) -> None:
        results = {
            "adf_test": TimeseriesTests.adf_test(self.historical_spread),
            "pp_test": TimeseriesTests.phillips_perron_test(self.historical_spread),
            "hurst_exponent": TimeseriesTests.hurst_exponent(self.historical_spread),
            "half_life": None,
        }

        # Calculate half-life and add to results
        results["half_life"], _ = TimeseriesTests.half_life(
            pd.Series(self.historical_spread)
        )

        # Log the results
        self.logger.info(
            f"{TimeseriesTests.display_adf_results({"spread": results["adf_test"]}, False)}\n"
        )
        self.logger.info(
            f"{TimeseriesTests.display_pp_results({"spread": results["pp_test"]}, False)}\n"
        )
        self.logger.info(f"\nHurst Exponent: {results['hurst_exponent']}\n")
        self.logger.info(f"\nHalf-Life: {results['half_life']}\n")

    # -- Strategy logic --
    def _update_spread(self, new_data: pd.DataFrame) -> None:
        """
        Update the historical spread based on the new data by applying the hedge ratios to the data.

        Parameters:
        - new_data (pandas.DataFrame) : Contains new data, assumes already adjusted to value of the asset.
        """
        # Convert the hedge ratio dictionary to a pandas Series
        cointegration_series = pd.Series(self.hedge_ratio)
        # print(cointegration_series)

        # Ensure the new_data DataFrame is aligned with the cointegration vector
        aligned_new_data = new_data[cointegration_series.index]
        # print(aligned_new_data)

        # Calculate the new spread value
        new_spread_value = aligned_new_data.dot(cointegration_series)
        # self.historical_data['spread'] = new_spread_value

        # Append the new spread value to the historical spread list
        self.historical_spread.append(new_spread_value.item())

    def _update_zscore(self, lookback_period: int = None) -> None:
        """
        Updates the historical z-score appending the end of the list, as well as updating the instance value of
        current  z-score.

        Parameters:
        - lookback_period (int) : Time period lookback to determine the z-score. If none passed will use all of historical spread.
        """
        # Determine the lookback range for the z-score calculation
        spread_lookback = (
            self.historical_spread[-lookback_period:]
            if lookback_period
            else self.historical_spread
        )

        # Calculate and append the new z-score
        self.current_zscore = self._calculate_single_zscore(spread_lookback)
        # self.historical_data['z-score'] = self.current_zscore

        # Update current z-score
        self.historical_zscore.append(self.current_zscore)

    def _calculate_single_zscore(self, spread_lookback: list) -> float:
        """
        Takes in the spread as a list and calculates the current z-score.

        Parameters:
        - spread_lookback (list) : A list of the rolling spread values.

        Returns:
        - float : Representing the z-score based on the given spread.
        """
        if len(spread_lookback) < 2:
            return 0
        mean = np.mean(spread_lookback)
        std = np.std(spread_lookback)
        return (spread_lookback[-1] - mean) / std if std != 0 else 0

    def _entry_signal(self, z_score: float, entry_threshold: float) -> bool:
        """
        Entry logic.

        Parameters:
        - z_score (float): Current value of the z-score.
        - entry_threshold (float): Absolute value of z-score that triggers an entry signal.

        Returns:
        - bool : True if an entry signal else False.
        """
        if not any(
            ticker in self.portfolio_server.positions
            for ticker in self.symbols_map.keys()
        ):
            if z_score >= entry_threshold:  # overvalued
                self.last_signal = Signal.Overvalued
                self.logger.info(
                    f"\nEntry Signal:\n  action : {self.last_signal}\n  z_score : {z_score}\n  entry_threshold : {entry_threshold}\n"
                )
                return True
            elif z_score <= -entry_threshold:
                self.last_signal = Signal.Undervalued
                self.logger.info(
                    f"\nEntry Signal:\n  action : {self.last_signal}\n  z_score : {z_score}\n  entry_threshold : {entry_threshold}\n"
                )
                return True
        else:
            return False

    def _exit_signal(self, z_score: float, exit_threshold: float) -> bool:
        """
        Exit logic.

        Parameters:
        - z_score (float): Current value of the z-score.
        - exit_threshold (float): Absolute value of z-score that triggers an exit signal.

        Returns:
        - bool : True if an exit signal else False.
        """
        if any(
            ticker in self.portfolio_server.positions
            for ticker in self.symbols_map.keys()
        ):
            if self.last_signal == Signal.Undervalued and z_score >= -exit_threshold:
                self.last_signal = Signal.Exit_Undervalued
                self.logger.info(
                    f"\nExit Signal:\n  action : {self.last_signal}\n  z_score : {z_score}\n  exit_threshold : {exit_threshold}\n"
                )
                return True
            elif self.last_signal == Signal.Overvalued and z_score <= exit_threshold:
                self.last_signal = Signal.Exit_Overvalued
                self.logger.info(
                    f"\nExit Signal:\n  action : {self.last_signal}\n  z_score : {z_score}\n  exit_threshold : {exit_threshold}\n"
                )
                return True
        else:
            return False

    def trade_capital(self, trade_allocation: float) -> float:
        """
        Determines the amount of capital allocated for a given signal.

        Parameters:
        - trade_allocation (float) : Percentage of all cash avialable that will be allocated for the trades from a given signal.

        Return:
        - float : The dollar value allocated.
        """
        trade_capital = self.portfolio_server.capital * trade_allocation
        self.logger.info(f"\nTRADE CAPITAL ALLOCATION : {trade_capital}\n")
        return trade_capital

    def generate_trade_instructions(
        self, signal: Signal, trade_capital: float
    ) -> List[TradeInstruction]:
        """
        Generate trade instructions list.

        Parameters:
        - signal (Signal): Enum value representing the direction of the signal.

        Returns:
        - List[TradeInstruction] : A list of objects of the trade instructions.
        """

        if signal in [Signal.Overvalued, Signal.Undervalued]:
            quantities = self.order_quantities_on_margin(trade_capital)
        else:
            quantities = {}
            for ticker, position in self.portfolio_server.positions.items():
                quantities[ticker] = abs(position.quantity)

        self.logger.info(quantities)

        trade_instructions = []
        leg_id = 1

        for ticker, hedge_ratio in self.hedge_ratio.items():
            if signal in [Signal.Overvalued, Signal.Exit_Undervalued]:
                if hedge_ratio < 0:
                    action = (
                        Action.LONG if signal == Signal.Overvalued else Action.COVER
                    )
                    quantity = quantities[ticker]
                    hedge_ratio = abs(hedge_ratio)
                else:
                    action = (
                        Action.SHORT if signal == Signal.Overvalued else Action.SELL
                    )
                    quantity = -quantities[ticker]
                    hedge_ratio = -abs(hedge_ratio)
            elif signal in [Signal.Undervalued, Signal.Exit_Overvalued]:
                if hedge_ratio > 0:
                    action = (
                        Action.LONG if signal == Signal.Undervalued else Action.COVER
                    )
                    quantity = quantities[ticker]
                else:
                    action = (
                        Action.SHORT if signal == Signal.Undervalued else Action.SELL
                    )
                    quantity = -quantities[ticker]

            trade_instructions.append(
                TradeInstruction(
                    ticker=ticker,
                    order_type=OrderType.MARKET,
                    action=action,
                    trade_id=self.trade_id,
                    leg_id=leg_id,
                    weight=hedge_ratio,
                    quantity=quantity,
                )
            )
            leg_id += 1

        return trade_instructions

    def order_quantities_on_margin(self, trade_capital: float):
        quantities = {}

        for ticker, percent in self.asset_allocation.items():
            trade_allocation = trade_capital * percent
            quantities[ticker] = math.floor(
                trade_allocation / self.symbols_map[ticker].initial_margin
            )

        return quantities

    def order_quantities_on_notional(self, trade_capital: float):
        quantities = {}
        for ticker, percent in self.asset_allocation.items():
            ticker_allocation = trade_capital * percent
            price = self.order_book.current_price(ticker)
            notional_value = (
                price
                * self.symbols_map[ticker].price_multiplier
                * self.symbols_map[ticker].quantity_multiplier
            )
            quantities[ticker] = math.floor(ticker_allocation / notional_value)

        return quantities

    def _order_quantity(
        self,
        action: Action,
        ticker: str,
        order_allocation: float,
        current_price: float,
        price_multiplier: float,
        quantity_multiplier: int,
    ) -> float:
        """
        Calculate the order quantity based on allocation, price, and multipliers.

        Parameters:
        - action (Action): The trading action (LONG, SHORT, SELL, COVER).
        - ticker (str): The ticker symbol for the order.
        - order_allocation (float): The capital allocated for this order.
        - current_price (float): The current price of the ticker.
        - price_multiplier (float): The price adjustment factor for the ticker.
        - quantity_multiplier (int): The quantity adjustment factor for the ticker.

        Returns:
        - float: The calculated quantity for the order.
        """
        # Adjust current price based on the price multiplier
        adjusted_price = current_price * price_multiplier

        # Adjust quantity based on the trade allocation
        if action in [Action.LONG, Action.SHORT]:  # Entry signal
            quantity = order_allocation / (adjusted_price * quantity_multiplier)
            # quantity *= 1 if action == Action.LONG else -1
        elif action in [Action.SELL, Action.COVER]:  # Exit signal
            quantity = self.portfolio_server.positions[ticker].quantity
            # quantity *= 1 if action == Action.COVER else -1
        return quantity

    def handle_market_data(self):
        """
        Entry class to handle the arrival of new market data. Creates a signal event that is then added to the
        event queue for processing.
        """
        # Initialize to null
        trade_instructions = None

        # Get current prices from order_book class
        close_values = self.order_book.current_prices()
        data = pd.DataFrame([close_values], index=[self.order_book.last_updated])
        self.historical_data = pd.concat(
            [self.historical_data, data], ignore_index=False
        )

        # Log price data
        log_data = self._log_prices(data)

        # Update features
        self._update_spread(log_data)
        self._update_zscore(self.zscore_lookback_period)

        if self._exit_signal(self.current_zscore, self.exit_threshold):
            trade_capital = self.trade_capital(self.trade_allocation)
            trade_instructions = self.generate_trade_instructions(
                self.last_signal, trade_capital
            )
            self.trade_id += 1
            self.last_signal = None
        elif self._entry_signal(self.current_zscore, self.entry_threshold):
            trade_capital = self.trade_capital(self.trade_allocation)
            trade_instructions = self.generate_trade_instructions(
                self.last_signal, trade_capital
            )

        if trade_instructions:
            self.set_signal(trade_instructions, self.order_book.last_updated)

    def get_strategy_data(self) -> pd.DataFrame:
        """
        Get strategy-specific data.
        """
        self.historical_data["spread"] = self.historical_spread
        self.historical_data["z-score"] = self.historical_zscore
        self.historical_data = self.historical_data.reset_index().rename(
            columns={"index": "timestamp"}
        )
        self._convert_timestamp(self.historical_data, "timestamp")
        return self.historical_data

    def _convert_timestamp(self, df: pd.DataFrame, column: str = "timestamp") -> None:
        df[column] = pd.to_datetime(df[column].map(lambda x: unix_to_iso(x, "EST")))
        df[column] = df[column].dt.tz_convert("America/New_York")
        df[column] = df[column].dt.tz_localize(None)

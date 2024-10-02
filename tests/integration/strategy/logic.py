import math
import numpy as np
import pandas as pd
from enum import Enum, auto
from typing import List, Dict, Tuple
from mbn import BufferStore, OhlcvMsg
from midas.engine.components.order_book import OrderBook
from midas.engine.components.base_strategy import BaseStrategy
from midas.engine.components.portfolio_server import PortfolioServer
from midas.signal import TradeInstruction, OrderType, Action
from midas.symbol import SymbolMap
from midas.engine.events.market_event import MarketEvent
from quantAnalytics.dataprocessor import DataProcessor
from midas.engine.components.observer.base import Subject, EventType


class Signal(Enum):
    """Long and short are treated as entry actions and short/cover are treated as exit actions."""

    Overvalued = auto()
    Undervalued = auto()
    Exit_Overvalued = auto()
    Exit_Undervalued = auto()
    NoSignal = auto()


class Cointegrationzscore(BaseStrategy):
    def __init__(
        self,
        symbols_map: SymbolMap,
        portfolio_server: PortfolioServer,
        order_book: OrderBook,
    ):

        # Initialize base
        super().__init__(symbols_map, portfolio_server, order_book)

        # Parameters
        self.trade_id = 1
        self.zscore_lookback = 10
        self.entry_threshold = 2
        self.exit_threshold = 1
        self.weights = {43: -3, 70: 2}  # HE:  , ZC:
        self.signal_allocation = 0.5

        # Strategy data
        self.data: pd.DataFrame
        self.spread = []
        self.zscore = []
        self.last_signal = Signal.NoSignal
        self.current_price: pd.DataFrame
        self.last_update_time = {
            symbol: None for symbol in self.weights.keys()
        }

    def prepare(self, data_buffer: BufferStore) -> None:
        # Process data
        self.data = data_buffer.decode_to_df(pretty_ts=False, pretty_px=True)

        self.data.drop(
            columns=["length", "rtype", "instrument_id"],
            inplace=True,
        )

        # Map symbols to id
        self.data["symbol"] = self.data["symbol"].map(
            self.symbols_map.midas_map
        )

        self.data = DataProcessor.align_timestamps(self.data, "drop")
        self.data = self.data.pivot(
            index="ts_event",
            columns="symbol",
            values="close",
        )
        self.data.columns = self.data.columns.astype(str)
        self.data.dropna(inplace=True)

        # Adjust to log
        self.data = self._log_transform(self.data)

        # Spread
        self.update_spread(self.data)

        # Z-score
        self.update_zscore(True)

        # Current price dataframe
        self.current_price = self.data.iloc[[-1]].copy(deep=True)

    def _log_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Log-transform the prices of the input data.
        """
        for column in data.columns:
            log_column_name = f"{column}_log"
            data[log_column_name] = np.log(data[column])
        return data

    def update_spread(self, data: pd.DataFrame) -> None:
        """
        Calculate the historical spread using the hedge ratios (weights).
        The spread is a weighted combination of the log prices of the instruments.
        """
        # Weighted sum of log prices
        spread_series = sum(
            self.weights[symbol] * data[f"{symbol}_log"]
            for symbol in self.weights
        )

        # Append the new spread to the instance variable
        self.spread.extend(spread_series.tolist())

    def update_zscore(self, initial: bool = False) -> np.ndarray:
        # Convert the current spread to a pandas Series
        spread_series = pd.Series(self.spread)

        if self.zscore_lookback:
            # Use a rolling window if lookback_period is specified
            mean = spread_series.rolling(window=self.zscore_lookback).mean()
            std = spread_series.rolling(window=self.zscore_lookback).std()
        else:
            # Use an expanding window if lookback_period is None, considering all data up to each point
            mean = spread_series.expanding().mean()
            std = spread_series.expanding().std()

        # Calculate z-score
        historical_zscore = ((spread_series - mean) / std).to_numpy()

        if initial:
            # Append the new z-score to the instance variable
            self.zscore.extend(historical_zscore.tolist())
        else:
            self.zscore.extend([historical_zscore[-1]])

    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        event: MarketEvent,
    ):

        if event_type == EventType.ORDER_BOOK:
            # prinst(event.data)
            if isinstance(event.data, OhlcvMsg):
                # Update the respective columns in `self.current_price`
                close = event.data.close
                key = event.data.instrument_id
                self.logger.info(event.data.ts_event)

                self.current_price[f"{key}"] = close / 1e9
                self.current_price[f"{key}_log"] = np.log(close / 1e9)
                self.last_update_time[key] = event.data.ts_event
            else:
                self.logger.info("Strategy recieved the tick market event")
            # Check if all tickers have the same timestamp
            if self.check_timestamps_aligned():
                self.process_data(event.data.ts_event)

    def check_timestamps_aligned(self) -> bool:
        """
        Check if the last update time for all tickers is the same.
        Returns True if they are aligned, otherwise False.
        """
        self.logger.info(f"Checking timestamps :{self.last_update_time}")

        timestamps = set(self.last_update_time.values())
        return len(timestamps) == 1 and None not in timestamps

    def process_data(self, ts_event: int) -> None:
        # Create new row
        new_row = self.current_price.copy()
        new_row["timestamp"] = ts_event
        new_row.set_index("timestamp", inplace=True)
        self.data = pd.concat([self.data, new_row], ignore_index=False)

        # Update Zscore
        self.update_spread(self.current_price)
        self.update_zscore()

        # Check if both tickers are in session before generating signals
        all_in_session = all(
            self.symbols_map.map[symbol].in_day_session(ts_event)
            for symbol in self.weights.keys()
        )
        self.logger.info(f"All in session {all_in_session}")

        not_in_rolling_window = all(
            not self.symbols_map.map[symbol].in_rolling_window(ts_event)
            for symbol in self.weights.keys()
        )
        self.logger.info(f"None in rolling window : {not_in_rolling_window}")

        # Check Signal
        if (
            self.order_book.tickers_loaded
            and all_in_session
            and not_in_rolling_window
        ):
            self.generate_signals()

    def generate_signals(self):
        trade_instructions = None
        current_zscore = self.zscore[-1]

        if not self._has_open_positions():
            # Check for entry signal
            if self._entry_signal(current_zscore):
                trade_instructions = self.generate_trade_instructions(
                    self.last_signal
                )
        else:
            # Check for exit signal
            if self._exit_signal(current_zscore):
                trade_instructions = self.generate_trade_instructions(
                    self.last_signal
                )
                self.trade_id += 1
                self.last_signal = None

        if trade_instructions:
            self.set_signal(trade_instructions, self.order_book.last_updated)

    def _has_open_positions(self) -> bool:
        """Return True if any positions are currently open in the portfolio."""
        return any(
            ticker in self.portfolio_server.get_positions
            for ticker in self.weights.keys()
        )

    def _entry_signal(self, zscore: float) -> bool:
        """
        Determine if an entry signal should be triggered based on z-score and threshold.
        """
        if zscore >= self.entry_threshold:
            self.last_signal = Signal.Overvalued
        elif zscore <= -self.entry_threshold:
            self.last_signal = Signal.Undervalued
        else:
            return False
        self.logger.info(
            f"Entry Signal: {self.last_signal}, z-score: {zscore}"
        )
        return True

    def _exit_signal(self, zscore: float) -> bool:
        """
        Determine if an exit signal should be triggered based on z-score and threshold.
        """
        if (
            self.last_signal == Signal.Undervalued
            and zscore >= -self.exit_threshold
        ):
            self.last_signal = Signal.Exit_Undervalued
        elif (
            self.last_signal == Signal.Overvalued
            and zscore <= self.exit_threshold
        ):
            self.last_signal = Signal.Exit_Overvalued
        else:
            return False
        self.logger.info(f"Exit Signal: {self.last_signal}, z-score: {zscore}")
        return True

    def generate_trade_instructions(
        self, signal: Signal
    ) -> List[TradeInstruction]:
        """
        Generate trade instructions based on the current signal.
        """
        self.logger.info(" Generating the signal")
        trade_instructions = []
        quantities = self._get_order_quantities(signal)

        for instrument, weight in self.weights.items():
            action, quantity = self._determine_action_and_quantity(
                signal,
                instrument,
                weight,
                quantities[instrument],
            )
            trade_instructions.append(
                TradeInstruction(
                    instrument=instrument,
                    order_type=OrderType.MARKET,
                    action=action,
                    trade_id=self.trade_id,
                    leg_id=len(trade_instructions) + 1,
                    weight=weight,
                    quantity=quantity,
                )
            )
        return trade_instructions

    def _get_order_quantities(self, signal: Signal) -> Dict[str, float]:
        """
        Get the order quantities based on the signal type and trade capital.
        """
        trade_capital = self.trade_capital()
        if signal in [Signal.Overvalued, Signal.Undervalued]:
            return self.order_quantities_on_margin(trade_capital)
        else:
            return {
                ticker: abs(position.quantity)
                for ticker, position in self.portfolio_server.get_positions.items()
            }

    def _determine_action_and_quantity(
        self,
        signal: Signal,
        ticker: str,
        hedge_ratio: float,
        quantity: float,
    ) -> Tuple[Action, float]:
        """
        Determine the action and quantity for a trade based on the signal and hedge ratio.
        """

        # Determine action based on signal and hedge ratio
        if signal == Signal.Overvalued:
            # Overvalued means we expect the price to fall, so we short if hedge_ratio > 0, otherwise we long.
            action = Action.SHORT if hedge_ratio > 0 else Action.LONG
            quantity *= -1 if hedge_ratio > 0 else 1
        elif signal == Signal.Undervalued:
            # Undervalued means we expect the price to rise, so we long if hedge_ratio > 0, otherwise we short.
            action = Action.LONG if hedge_ratio > 0 else Action.SHORT
            quantity *= 1 if hedge_ratio > 0 else -1

        elif signal == Signal.Exit_Overvalued:
            # Exit Overvalued means we are exiting a short position (SELL) or covering a long position (COVER)
            action = Action.COVER if hedge_ratio > 0 else Action.SELL
            quantity *= 1 if hedge_ratio > 0 else -1

        elif signal == Signal.Exit_Undervalued:
            # Exit Undervalued means we are exiting a long position (COVER) or selling a short position (SELL)
            action = Action.SELL if hedge_ratio > 0 else Action.COVER
            quantity *= -1 if hedge_ratio > 0 else 1

        return action, quantity

    def trade_capital(self) -> float:
        """
        Determines the amount of capital allocated for a given signal.

        Parameters:
        - trade_allocation (float) : Percentage of all cash avialable that will be allocated for the trades from a given signal.

        Return:
        - float : The dollar value allocated.
        """
        trade_capital = self.portfolio_server.capital * self.signal_allocation
        self.logger.info(f"\nTRADE CAPITAL ALLOCATION : {trade_capital}\n")
        return trade_capital

    def order_quantities_on_margin(self, trade_capital: float):
        quantities = {}
        weight_sum = sum(map(abs, self.weights.values()))

        for instrument_id, weight in self.weights.items():
            percent = abs(weight) / weight_sum
            trade_allocation = trade_capital * percent
            quantities[instrument_id] = math.floor(
                trade_allocation
                / self.symbols_map.map[instrument_id].initial_margin
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

    def get_strategy_data(self) -> pd.DataFrame:
        """
        Get strategy-specific data.
        """
        self.data["spread"] = self.spread
        self.data["z-score"] = self.zscore
        self.data = self.data.reset_index().rename(
            columns={"index": "timestamp"}
        )
        return self.data

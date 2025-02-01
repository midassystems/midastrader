import math
import numpy as np
import pandas as pd
from enum import Enum, auto
from typing import List, Dict, Tuple
from mbn import OhlcvMsg

from midastrader.message_bus import MessageBus
from midastrader.structs import SymbolMap, SignalInstruction, OrderType, Action
from midastrader.structs.events import MarketEvent
from midastrader.core import BaseStrategy


class Signal(Enum):
    """Long and short are treated as entry actions and short/cover are treated as exit actions."""

    Overvalued = auto()
    Undervalued = auto()
    Exit_Overvalued = auto()
    Exit_Undervalued = auto()
    NoSignal = auto()


class Cointegrationzscore(BaseStrategy):
    def __init__(self, symbols_map: SymbolMap, bus: MessageBus):

        # Initialize base
        super().__init__(symbols_map, bus)

        # Parameters
        self.signal_id = 1
        self.zscore_lookback = 10
        self.entry_threshold = 2
        self.exit_threshold = 1
        self.weights = {43: -3, 70: 2}  # HE:  , ZC:
        self.signal_allocation = 0.5

        # Strategy data
        self.data = pd.DataFrame()
        self.spread = []
        self.zscore = []
        self.last_signal = Signal.NoSignal
        self.last_update_time = {symbol: None for symbol in self.weights}

        self.current_price = self.initialize_current_price()

    # Data Processing
    def initialize_current_price(self) -> pd.DataFrame:
        """
        Initialize `self.current_price` with a single row and placeholder values.
        """
        initial_data = {f"{key}": 0 for key in self.weights.keys()}
        initial_data.update({f"{key}_log": 0 for key in self.weights.keys()})
        return pd.DataFrame([initial_data])

    def handle_event(self, event: MarketEvent):
        # self.logger.info(f"{len(self.data)}")
        # self.logger.info(event)

        if isinstance(event.data, OhlcvMsg):
            self.update_current_price(event.data)
        else:
            self.logger.info("Strategy received a tick market event.")

        if self.check_timestamps_aligned():
            self.process_data(event.data.ts_event)
        else:
            # Use set_signal to handle signal dispatch and flag toggling
            self.set_signal([], event.data.ts_event)

    def update_current_price(self, data: OhlcvMsg) -> None:
        """
        Update `self.current_price` with the latest price data.
        """
        close = data.close / 1e9
        key = data.instrument_id
        self.current_price[f"{key}"] = close
        self.current_price[f"{key}_log"] = np.log(close)
        self.last_update_time[key] = data.ts_event

    def check_timestamps_aligned(self) -> bool:
        """
        Check if the last update time for all tickers is the same.
            Returns True if they are aligned, otherwise False.
        """
        timestamps = set(self.last_update_time.values())
        return len(timestamps) == 1 and None not in timestamps

    def process_data(self, ts_event: int) -> None:
        # self.logger.info("Aligned timestamps. Processing data...")

        # Update historical data
        self.update_data(ts_event)

        # Update spread and z-score
        self.update_spread()
        self.update_zscore()

        # Generate Signal
        self.generate_signals(ts_event)

    def update_data(self, ts_event: int) -> None:
        """
        Add the current price data to the historical data log.
        """
        new_row = self.current_price.copy()
        new_row["timestamp"] = ts_event
        new_row.set_index("timestamp", inplace=True)
        self.data = pd.concat([self.data, new_row], ignore_index=False)

    def update_spread(self) -> None:
        """
        Calculate the historical spread using the hedge ratios (weights).
        The spread is a weighted combination of the log prices of the instruments.
        """
        # Weighted sum of log prices
        spread_series = sum(
            self.weights[symbol] * self.current_price[f"{symbol}_log"]
            for symbol in self.weights
        )

        # Append the new spread to the instance variable
        self.spread.extend(spread_series.tolist())

    def update_zscore(self) -> None:
        """
        Update the Z-score based on the spread.
        """
        spread_series = pd.Series(self.spread)
        mean = spread_series.rolling(window=self.zscore_lookback).mean()
        std = spread_series.rolling(window=self.zscore_lookback).std()
        self.zscore.append(
            ((spread_series.iloc[-1] - mean.iloc[-1]) / std.iloc[-1])
        )

    # Generate Signals
    def generate_signals(self, ts_event: int):
        current_zscore = self.zscore[-1]
        self.logger.info(f"zscore : {current_zscore}")

        trade_instructions = []
        if self.is_valid_for_signal_generation(ts_event):
            # self.logger.info("Checking signals.")
            if not self._has_open_positions():
                # self.logger.info("No positions")
                # Check for entry signal
                if self._entry_signal(current_zscore):
                    trade_instructions.extend(
                        self.create_trade_instructions(self.last_signal)
                    )
            else:
                # Check for exit signal
                if self._exit_signal(current_zscore):
                    trade_instructions.extend(
                        self.create_trade_instructions(self.last_signal)
                    )
                    self.signal_id += 1
                    self.last_signal = None

        # self.logger.info("Calling set signal")
        self.set_signal(
            trade_instructions,
            self.order_book.last_updated,
        )

    def is_valid_for_signal_generation(self, ts_event: int) -> bool:
        """
        Validate whether the current state allows for signal generation.
        """
        # not_expired = self.check_futures_expiration_window(ts_event)
        return (
            self.order_book.tickers_loaded
            # and not_expired
            and len(self.spread) > self.zscore_lookback
        )

    def check_in_day_session(self, ts_event: int) -> bool:
        return all(
            self.symbols_map.map[symbol].in_day_session(ts_event)
            for symbol in self.weights.keys()
        )

    def check_futures_expiration_window(self, ts_event: int) -> bool:
        """
        Ensure none of the tickers are within their rolling expiration window.
        """
        return all(
            not self.symbols_map.map[symbol].in_rolling_window(ts_event)
            for symbol in self.weights
        )

    def _has_open_positions(self) -> bool:
        """Return True if any positions are currently open in the portfolio."""
        return any(
            ticker in self.portfolio_server.positions
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

        self.logger.info(f"Entry Signal: {self.last_signal} zscore: {zscore}")
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
        self.logger.info(f"Exit Signal: {self.last_signal} zscore: {zscore}")
        return True

    # Trade Instructions
    def create_trade_instructions(
        self,
        signal: Signal,
    ) -> List[SignalInstruction]:
        """
        Generate trade instructions based on the current signal.
        """
        quantities = self.get_order_quantities(signal)
        trade_instructions = []

        for instrument, weight in self.weights.items():
            try:
                self.logger.info(quantities)
                self.logger.info(quantities[instrument])
            except Exception as e:
                self.logger.info(f"error here - {e}")

            action, quantity = self.get_action_and_quantity(
                signal,
                instrument,
                weight,
                quantities[instrument],
            )
            trade_instructions.append(
                SignalInstruction(
                    instrument=instrument,
                    order_type=OrderType.MARKET,
                    action=action,
                    signal_id=self.signal_id,
                    # leg_id=len(trade_instructions) + 1,
                    weight=weight,
                    quantity=float(quantity),
                )
            )
        return trade_instructions

    def get_order_quantities(self, signal: Signal) -> Dict[str, float]:
        """
        Calculate order quantities based on the signal type and available capital.
        """
        trade_capital = self.trade_capital()
        if signal in [Signal.Overvalued, Signal.Undervalued]:
            return self.order_quantities_on_margin(trade_capital)
        return {
            ticker: abs(position.quantity)
            for ticker, position in self.portfolio_server.positions.items()
        }

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

    def get_action_and_quantity(
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

    def get_strategy_data(self) -> pd.DataFrame:
        """
        Get strategy-specific data.
        """
        self.data["spread"] = self.spread
        self.data["z-score"] = self.zscore
        # self.data["z-score"] = [np.nan] * (self.zscore_lookback - 1) + list(
        #     self.zscore
        # )
        # self.data = self.data.reset_index().rename(
        #     columns={"index": "timestamp"}
        # )
        self.data.reset_index(inplace=True)
        self.data.rename(columns={"index": "timestamp"}, inplace=True)
        return self.data

    # def process_data(self, ts_event: int) -> None:
    #     self.logger.info("Strategy - Aligned ts Processing data.")
    #
    #     # Update data log
    #     new_row = self.current_price.copy()
    #     new_row["timestamp"] = ts_event
    #     new_row.set_index("timestamp", inplace=True)
    #     self.data = pd.concat([self.data, new_row], ignore_index=False)
    #
    #     # Updated spread
    #     self.update_spread(self.current_price)
    #
    #     if len(self.spread) < self.zscore_lookback:
    #         return
    #
    #     # Update Zscore
    #     self.update_zscore()
    #
    #     # all_in_session = all(
    #     #     self.symbols_map.map[symbol].in_day_session(ts_event)
    #     #     for symbol in self.weights.keys()
    #     # )
    #     # self.logger.debug(f"All in session {all_in_session}")
    #     # Check if both tickers are in session before generating signals
    #     day_session = self.check_in_day_session(ts_event)
    #     not_expiration_window = self.check_futures_expiration_window(ts_event)
    #
    #     # not_in_rolling_window = all(
    #     #     not self.symbols_map.map[symbol].in_rolling_window(ts_event)
    #     #     for symbol in self.weights.keys()
    #     # )
    #     # self.logger.debug(f"None in rolling window : {not_in_rolling_window}")
    #
    #     # Check Signal
    #     if (
    #         self.order_book.tickers_loaded
    #         and day_session
    #         and not_expiration_window
    #     ):
    #         self.generate_signals()

    # def primer(self, record: mbn.RecordMsg) -> None:
    #     # pass
    #     # self.data = pd.DataFrame()
    #     # self.initialize_current_price()
    #     #
    #     # while True:
    #     # record = self.hist_data_client.next_record()
    #
    #     # if not record:
    #     #     raise RuntimeError("Not enough records to prime strategy.")
    #
    #     # if record:
    #     key = record.instrument_id
    #     self.current_price[f"{key}"] = record.close / 1e9
    #     self.current_price[f"{key}_log"] = np.log(record.close / 1e9)
    #     self.last_update_time[key] = record.ts_event
    #
    #     # Check if all tickers have the same timestamp
    #     if self.check_timestamps_aligned():
    #         # Create new row
    #         new_row = self.current_price.copy()
    #         new_row["timestamp"] = record.ts_event
    #         new_row.set_index("timestamp", inplace=True)
    #         self.data = pd.concat([self.data, new_row], ignore_index=False)
    #
    #     if len(self.data) == self.zscore_lookback:
    #         break
    #
    #     # Spread
    #     self.update_spread(self.data)
    #
    #     # Z-score
    #     self.update_zscore(True)

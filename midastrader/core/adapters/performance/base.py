import mbn
import math
import queue
import threading
import pandas as pd
from datetime import datetime
from mbn import BacktestData
from midas_client.client import DatabaseClient

from midastrader.structs.symbol import SymbolMap
from midastrader.config import Parameters, Mode
from midastrader.core.adapters.base_strategy import BaseStrategy
from midastrader.utils.unix import unix_to_iso
from midastrader.structs.constants import PRICE_FACTOR
from midastrader.message_bus import MessageBus, EventType
from midastrader.structs.events import TradeCommissionEvent, TradeEvent
from midastrader.core.adapters.base import CoreAdapter
from .managers import (
    AccountManager,
    EquityManager,
    TradeManager,
    SignalManager,
)


def replace_nan_inf_in_dict(d: dict) -> None:
    """
    Replaces NaN and infinity values in a dictionary (nested structures are supported) with 0.0.

    Args:
        d (dict): A dictionary possibly containing NaN or infinite values.
    """
    for key, value in d.items():
        if isinstance(value, dict):
            replace_nan_inf_in_dict(value)
        elif isinstance(value, float) and (
            math.isnan(value) or math.isinf(value)
        ):
            d[key] = 0.0


def _convert_timestamp(df: pd.DataFrame, column: str = "ts_event") -> None:
    """
    Converts a timestamp column to localized datetime in New York timezone.

    Args:
        df (pd.DataFrame): The DataFrame containing the timestamp column.
        column (str): The name of the timestamp column to convert. Defaults to "ts_event".
    """
    df[column] = pd.to_datetime(df[column].map(lambda x: unix_to_iso(x)))
    df[column] = df[column].dt.tz_convert("America/New_York")
    df[column] = df[column].dt.tz_localize(None)


class PerformanceManager(CoreAdapter):
    """
    Manages and tracks the performance of trading strategies.

    The `PerformanceManager` collects and logs performance data, including signals, trades,
    equity changes, and account updates. It interacts with various managers to store and
    process performance-related information.
    """

    def __init__(
        self,
        symbols_map: SymbolMap,
        bus: MessageBus,
        params: Parameters,
        mode: Mode,
        output_dir: str,
    ) -> None:
        """
        Initializes the PerformanceManager with necessary components.

        Args:
            database (DatabaseClient): Client for database operations related to performance data.
            params (Parameters): Configuration parameters for performance tracking.
            symbols_map (SymbolMap): Mapping of instrument symbols to `Symbol` objects.
        """
        super().__init__(symbols_map, bus)
        self.trade_manager = TradeManager(self.logger)
        self.equity_manager = EquityManager(self.logger)
        self.signal_manager = SignalManager(self.logger)
        self.account_manager = AccountManager(self.logger)
        self.database = DatabaseClient()
        self.params = params
        self.mode = mode
        self.output_dir = output_dir
        self.strategy: BaseStrategy = None
        self.threads = []
        self.running = threading.Event()

        # Subscribe to events
        self.account_queue = self.bus.subscribe(EventType.ACCOUNT_UPDATE_LOG)
        self.equity_queue = self.bus.subscribe(EventType.EQUITY_UPDATE)
        self.signal_queue = self.bus.subscribe(EventType.SIGNAL_UPDATE)
        self.trade_queue = self.bus.subscribe(EventType.TRADE_UPDATE)
        self.trade_commission_queue = self.bus.subscribe(
            EventType.TRADE_COMMISSION_UPDATE
        )

    def set_strategy(self, strategy: BaseStrategy) -> None:
        """
        Sets the strategy for performance tracking.

        Args:
            strategy (BaseStrategy): The trading strategy to track performance for.
        """
        self.strategy = strategy

    def process(self):
        try:
            # Start sub-threads
            self.threads.append(
                threading.Thread(target=self.process_account, daemon=True)
            )
            self.threads.append(
                threading.Thread(target=self.process_trades, daemon=True)
            )
            self.threads.append(
                threading.Thread(target=self.process_equity, daemon=True)
            )
            self.threads.append(
                threading.Thread(target=self.process_signal, daemon=True)
            )

            for thread in self.threads:
                thread.start()

            self.logger.info("Performancemanager running ...")
            self.running.set()

            for thread in self.threads:
                thread.join()
        finally:
            # Always call cleanup on exit
            self.cleanup()

    def cleanup(self):
        self.save()
        self.logger.info("Shutting down order execution manager...")

    def process_account(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        while not self.shutdown_event.is_set():
            try:
                item = self.account_queue.get()
                self.account_manager.update_account_log(item)
            except queue.Empty:
                continue

    def process_trades(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        while not self.shutdown_event.is_set():
            try:

                item = self.trade_queue.get()
                if isinstance(item, TradeEvent):
                    self.trade_manager.update_trades(item)

                if isinstance(item, TradeCommissionEvent):
                    self.trade_manager.update_trade_commission(item)

            except queue.Empty:
                continue

    def process_equity(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        while not self.shutdown_event.is_set():
            try:
                item = self.equity_queue.get()
                self.equity_manager.update_equity(item)
            except queue.Empty:
                continue

    def process_signal(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        while not self.shutdown_event.is_set():
            try:
                item = self.signal_queue.get()
                self.signal_manager.update_signals(item)
            except queue.Empty:
                continue

    def export_results(self, static_stats: dict, output_path: str) -> None:
        """
        Exports performance results, including static statistics, trades, equity, and signals,
        into an Excel workbook.

        This method consolidates various performance metrics, including static statistics,
        aggregated trade data, equity statistics, signals, and strategy-specific data,
        and writes them to separate sheets in an Excel file.

        Args:
            static_stats (dict): A dictionary containing static performance statistics.
            output_path (str): The file path where the Excel workbook will be saved.

        Behavior:
            - Static statistics are written to the "Static Stats" sheet.
            - Strategy parameters, trades, equity data (daily and period), and signals are exported.
            - Each dataset is converted into a structured DataFrame and timestamps are localized.
            - The resulting Excel file contains multiple sheets with organized performance data.
        """
        # Summary Stats
        static_stats_df = pd.DataFrame([static_stats]).T

        # Parameters
        params_df = pd.DataFrame(self.params.to_dict())
        params_df["tickers"] = ", ".join(params_df["tickers"])
        params_df = params_df.iloc[0:1]

        columns = ["start", "end"]
        for column in columns:
            _convert_timestamp(params_df, column)
        params_df = params_df.T

        # Trades
        trades_df = pd.DataFrame(self.trade_manager.trades.values())
        _convert_timestamp(trades_df, "timestamp")

        agg_trade_df = self.trade_manager._aggregate_trades()
        _convert_timestamp(agg_trade_df, "start_date")
        _convert_timestamp(agg_trade_df, "end_date")

        # Equity
        period_df = self.equity_manager.period_stats.copy()
        _convert_timestamp(period_df, "timestamp")

        daily_df = self.equity_manager.daily_stats.copy()
        _convert_timestamp(daily_df, "timestamp")

        # Signals
        signals_df = self.signal_manager._flatten_trade_instructions()
        _convert_timestamp(signals_df, "timestamp")

        # Strategy
        strategy_data = self.strategy.get_strategy_data()
        if len(strategy_data) > 0:
            _convert_timestamp(strategy_data, "timestamp")

        with pd.ExcelWriter(
            output_path + "output.xlsx", engine="xlsxwriter"
        ) as writer:
            params_df.to_excel(writer, sheet_name="Parameters")
            static_stats_df.to_excel(writer, sheet_name="Static Stats")
            period_df.to_excel(writer, index=False, sheet_name="Period Equity")
            daily_df.to_excel(writer, index=False, sheet_name="Daily Equity")
            trades_df.to_excel(writer, index=False, sheet_name="Trades")
            agg_trade_df.to_excel(writer, index=False, sheet_name="Agg Trades")
            signals_df.to_excel(writer, index=False, sheet_name="Signals")
            strategy_data.to_excel(writer, index=False, sheet_name="Strategy")

    def save(self) -> None:
        """
        Saves the performance data based on the specified mode.

        This method delegates saving performance data to the appropriate sub-method based on
        whether the mode is `LIVE` or `BACKTEST`.

        Args:
            mode (Mode): The mode of the strategy (`Mode.LIVE` or `Mode.BACKTEST`).
            output_path (str, optional): The directory where the results will be saved. Defaults to an empty string.

        Raises:
            ValueError: If the mode is neither `LIVE` nor `BACKTEST`.
        """
        if self.mode == Mode.BACKTEST:
            self._save_backtest(self.output_dir)
        elif self.mode == Mode.LIVE:
            self._save_live(self.output_dir)

    def mbn_static_stats(self, static_stats: dict) -> mbn.StaticStats:
        """
        Converts static performance statistics into an `mbn.StaticStats` object.

        Behavior:
            - Scales all percentage and ratio metrics using a `PRICE_FACTOR`.
            - Creates an `mbn.StaticStats` object with all relevant performance statistics.

        Args:
            static_stats (dict): A dictionary containing static performance metrics.

        Returns:
            mbn.StaticStats: An instance of `mbn.StaticStats` with converted and scaled values.

        """
        return mbn.StaticStats(
            total_trades=static_stats["total_trades"],
            total_winning_trades=static_stats["total_winning_trades"],
            total_losing_trades=static_stats["total_losing_trades"],
            avg_profit=int(static_stats["avg_profit"] * PRICE_FACTOR),
            avg_profit_percent=int(
                static_stats["avg_profit_percent"] * PRICE_FACTOR
            ),
            avg_gain=int(static_stats["avg_gain"] * PRICE_FACTOR),
            avg_gain_percent=int(
                static_stats["avg_gain_percent"] * PRICE_FACTOR
            ),
            avg_loss=int(static_stats["avg_loss"] * PRICE_FACTOR),
            avg_loss_percent=int(
                static_stats["avg_loss_percent"] * PRICE_FACTOR
            ),
            profitability_ratio=int(
                static_stats["profitability_ratio"] * PRICE_FACTOR
            ),
            profit_factor=int(static_stats["profit_factor"] * PRICE_FACTOR),
            profit_and_loss_ratio=int(
                static_stats["profit_and_loss_ratio"] * PRICE_FACTOR
            ),
            total_fees=int(static_stats["total_fees"] * PRICE_FACTOR),
            net_profit=int(static_stats["net_profit"] * PRICE_FACTOR),
            beginning_equity=int(
                static_stats["beginning_equity"] * PRICE_FACTOR
            ),
            ending_equity=int(static_stats["ending_equity"] * PRICE_FACTOR),
            total_return=int(static_stats["total_return"] * PRICE_FACTOR),
            annualized_return=int(
                static_stats["annualized_return"] * PRICE_FACTOR
            ),
            daily_standard_deviation_percentage=int(
                static_stats["daily_standard_deviation_percentage"]
                * PRICE_FACTOR
            ),
            annual_standard_deviation_percentage=int(
                static_stats["annual_standard_deviation_percentage"]
                * PRICE_FACTOR
            ),
            max_drawdown_percentage_period=int(
                static_stats["max_drawdown_percentage_period"] * PRICE_FACTOR
            ),
            max_drawdown_percentage_daily=int(
                static_stats["max_drawdown_percentage_daily"] * PRICE_FACTOR
            ),
            sharpe_ratio=int(static_stats["sharpe_ratio"] * PRICE_FACTOR),
            sortino_ratio=int(static_stats["sortino_ratio"] * PRICE_FACTOR),
        )

    def generate_backtest_name(self) -> str:
        """
        Generates a unique backtest name based on the strategy name and current timestamp.

        Returns:
            str: A unique backtest name in the format `strategy_name-YYYYMMDDHHMMSS`.

        Example:
            If the strategy name is "MyStrategy" and the current datetime is 2024-12-18 10:30:45,
            the generated name will be `MyStrategy-20241218103045`.
        """
        c = datetime.today()
        return f"{self.params.strategy_name}-{c.year}{c.month}{c.day}{c.hour}{c.minute}{c.second}"

    def _save_backtest(self, output_path: str = "") -> None:
        """
        Saves the backtest performance data, including configuration, trades, signals, and equity statistics.

        Behavior:
            - Aggregates trade and equity statistics.
            - Exports performance data to an Excel file using `export_results`.
            - Creates a `BacktestData` object containing all backtest-related metrics and data.
            - Saves the backtest to the database using the `create_backtest` method of the database client.
            - Logs the result of the save operation.

        Args:
            output_path (str, optional): The directory path where the backtest results will be saved.
                Defaults to an empty string (current directory).

        Raises:
            RuntimeError: If the database save operation fails.
        """
        # Aggregate trades and equity statistics
        trade_stats = self.trade_manager.calculate_trade_statistics()
        equity_stats = self.equity_manager.calculate_equity_statistics(
            self.params.risk_free_rate
        )

        # Summary stats
        all_stats = {**trade_stats, **equity_stats}
        static_stats = all_stats

        # Export to Excel
        self.export_results(static_stats, output_path)

        # Create Backtest Object
        self.backtest = BacktestData(
            metadata=mbn.BacktestMetaData(
                backtest_id=0,  # dummy value server will assign a unique id
                backtest_name=self.generate_backtest_name(),
                parameters=self.params.to_mbn(),
                static_stats=self.mbn_static_stats(static_stats),
            ),
            period_timeseries_stats=self.equity_manager.period_stats_mbn,
            daily_timeseries_stats=self.equity_manager.daily_stats_mbn,
            trades=self.trade_manager.to_mbn(self.symbols_map),
            signals=self.signal_manager.to_mbn(self.symbols_map),
        )
        # Save Backtest Object
        response = self.database.trading.create_backtest(self.backtest)
        print(response)
        self.logger.info(f"Backtest saved with response : {response}")

    def mbn_account_summary(self, account: dict) -> mbn.AccountSummary:
        """
        Converts account summary data into an `mbn.AccountSummary` object.

        Behavior:
            - Scales monetary and percentage metrics using a `PRICE_FACTOR`.
            - Populates `mbn.AccountSummary` with fields for both start and end timestamps, buying power,
              liquidity, margin requirements, PnL, cash balance, and net liquidation values.

        Args:
            account (dict): A dictionary containing account-related metrics for both start and end states.

        Returns:
            mbn.AccountSummary: An instance of `mbn.AccountSummary` with scaled and converted account values.
        """
        return mbn.AccountSummary(
            currency=account["currency"],
            start_timestamp=int(account["start_timestamp"]),
            start_buying_power=int(
                account["start_buying_power"] * PRICE_FACTOR
            ),
            start_excess_liquidity=int(
                account["start_excess_liquidity"] * PRICE_FACTOR
            ),
            start_full_available_funds=int(
                account["start_full_available_funds"] * PRICE_FACTOR
            ),
            start_full_init_margin_req=int(
                account["start_full_init_margin_req"] * PRICE_FACTOR
            ),
            start_full_maint_margin_req=int(
                account["start_full_maint_margin_req"] * PRICE_FACTOR
            ),
            start_futures_pnl=int(account["start_futures_pnl"] * PRICE_FACTOR),
            start_net_liquidation=int(
                account["start_net_liquidation"] * PRICE_FACTOR
            ),
            start_total_cash_balance=int(
                account["start_total_cash_balance"] * PRICE_FACTOR
            ),
            start_unrealized_pnl=int(
                account["start_unrealized_pnl"] * PRICE_FACTOR
            ),
            end_timestamp=int(account["end_timestamp"]),
            end_buying_power=int(account["end_buying_power"] * PRICE_FACTOR),
            end_excess_liquidity=int(
                account["end_excess_liquidity"] * PRICE_FACTOR
            ),
            end_full_available_funds=int(
                account["end_full_available_funds"] * PRICE_FACTOR
            ),
            end_full_init_margin_req=int(
                account["end_full_init_margin_req"] * PRICE_FACTOR
            ),
            end_full_maint_margin_req=int(
                account["end_full_maint_margin_req"] * PRICE_FACTOR
            ),
            end_futures_pnl=int(account["end_futures_pnl"] * PRICE_FACTOR),
            end_net_liquidation=int(
                account["end_net_liquidation"] * PRICE_FACTOR
            ),
            end_total_cash_balance=int(
                account["end_total_cash_balance"] * PRICE_FACTOR
            ),
            end_unrealized_pnl=int(
                account["end_unrealized_pnl"] * PRICE_FACTOR
            ),
        )

    def _save_live(self, output_path: str = ""):
        """
        Processes and saves data from a live trading session into the database.

        Behavior:
            - Combines account log entries for start and end states into a single dictionary.
            - Converts account data into an `mbn.AccountSummary` object using `mbn_account_summary`.
            - Creates an `mbn.LiveData` object containing session parameters, trades, signals, and account summary.
            - Saves the live session data to the database via the `create_live_session` method.
            - Logs the results of the save operation.

        Args:
            output_path (str, optional): The directory path where logs or additional outputs can be saved.
                Defaults to an empty string.

        Raises:
            RuntimeError: If the database save operation fails.
        """
        # Create a dictionary of start and end account values
        combined_data = {
            **self.account_manager.account_log[0].to_dict(prefix="start_"),
            **self.account_manager.account_log[-1].to_dict(prefix="end_"),
        }

        # Create Live Summary Object
        self.live_summary = mbn.LiveData(
            parameters=self.params.to_mbn(),
            trades=self.trade_manager.to_mbn(self.symbols_map),
            signals=self.signal_manager.to_mbn(self.symbols_map),
            account=self.mbn_account_summary(combined_data),
        )

        # Save Live Summary Session
        response = self.database.trading.create_live(self.live_summary)
        self.logger.info(
            f"Live Session saved to database with response : {response}"
        )

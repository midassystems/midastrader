import math
import pandas as pd
from midas.utils.logger import SystemLogger
from midas.engine.config import Parameters, Mode
from midas.engine.components.observer.base import Observer, Subject, EventType
from midas.engine.components.base_strategy import BaseStrategy
from midas.utils.unix import unix_to_iso
from midasClient.client import DatabaseClient
from midas.constants import PRICE_FACTOR
import mbn
from mbn import BacktestData
from midas.symbol import SymbolMap
from midas.engine.components.performance.managers import (
    AccountManager,
    EquityManager,
    TradeManager,
    SignalManager,
)


def replace_nan_inf_in_dict(d):
    for key, value in d.items():
        if isinstance(value, dict):
            replace_nan_inf_in_dict(value)
        elif isinstance(value, float) and (
            math.isnan(value) or math.isinf(value)
        ):
            d[key] = 0.0


def _convert_timestamp(df: pd.DataFrame, column: str = "ts_event") -> None:
    df[column] = pd.to_datetime(df[column].map(lambda x: unix_to_iso(x)))
    df[column] = df[column].dt.tz_convert("America/New_York")
    df[column] = df[column].dt.tz_localize(None)


class PerformanceManager(Subject, Observer):
    """
    Base class for managing and tracking the performance of trading strategies.
    It collects and logs information about signals, trades, equity changes, and account updates.
    """

    def __init__(
        self,
        database: DatabaseClient,
        params: Parameters,
        symbols_map: SymbolMap,
    ) -> None:
        """
        Initializes the performance manager with necessary components for tracking and analysis.

        Parameters:
        - database (DatabaseClient): Client for database operations related to performance data.
        - logger (logging.Logger): Logger for recording activity and debugging.
        - params (Parameters): Configuration parameters for the performance manager.
        """
        Subject().__init__()
        self.logger = SystemLogger.get_logger()
        self.trade_manager = TradeManager(self.logger)
        self.equity_manager = EquityManager(self.logger)
        self.signal_manager = SignalManager(self.logger)
        self.account_manager = AccountManager(self.logger)
        self.strategy: BaseStrategy
        self.params = params
        self.symbols_map = symbols_map
        self.database = database

    def set_strategy(self, strategy: BaseStrategy):
        self.strategy = strategy

    def handle_event(
        self, subject: Subject, event_type: EventType, *args, **kwargs
    ) -> None:
        if event_type == EventType.EQUITY_VALUE_UPDATE:
            if len(args) == 1:
                self.equity_manager.update_equity(args[0])
            else:
                raise ValueError("Missing required arguments for EQUITY_EVENT")
        elif event_type == EventType.ACCOUNT_UPDATE:
            if len(args) == 1:
                self.account_manager.update_account_log(args[0])
            else:
                raise ValueError("Missing account details for ACCOUNT_UPDATE")
        elif event_type == EventType.TRADE_UPDATE:
            if len(args) == 2:
                self.trade_manager.update_trades(args[0], args[1])
            else:
                raise ValueError("Missing order data for TRADE_UPDATE")
        elif event_type == EventType.TRADE_COMMISSION_UPDATE:
            if len(args) == 2:
                self.trade_manager.update_trade_commission(args[0], args[1])
            else:
                raise ValueError(
                    "Missing order data for TRADE_COMMMISSION_UPDATE"
                )
        elif event_type == EventType.SIGNAL:
            if len(args) == 1:
                self.signal_manager.update_signals(args[0])
            else:
                raise ValueError("Missing order data for SIGNAL_UPDATE")

        else:
            raise ValueError(f"Unhandled event type: {event_type}")

    def export_results(self, static_stats: dict, output_path: str):
        # Summary Stats
        static_stats_df = pd.DataFrame([static_stats]).T

        # Parameters
        params_df = pd.DataFrame(self.params.to_dict())
        params_df["tickers"] = ", ".join(params_df["tickers"])
        params_df = params_df.iloc[0:1]

        columns = ["train_start", "test_start", "train_end", "test_end"]
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

    def save(self, mode: Mode, output_path: str = "") -> None:
        """
        Saves the performance data based on the mode (live or backtest).
        """
        if mode == Mode.BACKTEST:
            self._save_backtest(output_path)
        elif mode == Mode.LIVE:
            self._save_live(output_path)

    def mbn_static_stats(self, static_stats: dict) -> mbn.StaticStats:
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

    def _save_backtest(self, output_path: str = "") -> None:
        """
        Saves the collected performance data including the backtest configuration, trades, and signals
        to a database or other storage mechanism.
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
            backtest_id=None,
            backtest_name=self.params.backtest_name,
            parameters=self.params.to_mbn(),
            static_stats=self.mbn_static_stats(static_stats),
            period_timeseries_stats=self.equity_manager.period_stats_mbn,
            daily_timeseries_stats=self.equity_manager.daily_stats_mbn,
            trades=self.trade_manager.to_mbn(self.symbols_map),
            signals=self.signal_manager.to_mbn(self.symbols_map),
        )
        # Save Backtest Object
        response = self.database.trading.create_backtest(self.backtest)
        self.logger.info(f"Backtest saved with response : {response}")

    def mbn_account_summary(self, account: dict) -> mbn.AccountSummary:
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
        Processes and saves the collected data from the live trading session into the database.
        """
        # Create a dictionary of start and end account values
        combined_data = {
            **self.account_manager.account_log[0].to_dict(prefix="start_"),
            **self.account_manager.account_log[-1].to_dict(prefix="end_"),
        }
        self.logger.info(f"Account Data {combined_data}")

        # Create Live Summary Object
        self.live_summary = mbn.LiveData(
            parameters=self.params.to_mbn(),
            trades=self.trade_manager.to_mbn(self.symbols_map),
            signals=self.signal_manager.to_mbn(self.symbols_map),
            account=self.mbn_account_summary(combined_data),
        )

        # Save Live Summary Session
        response = self.database.create_live_session(self.live_summary)
        self.logger.info(
            f"Live Session= saved to data base with response : {response}"
        )

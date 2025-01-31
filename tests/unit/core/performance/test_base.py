import mbn
import unittest
import pandas as pd
import random
from time import sleep
import threading
from datetime import time
from unittest.mock import Mock, MagicMock

from midastrader.structs.events.market_event import MarketEvent
from midastrader.structs.symbol import SymbolMap
from midastrader.utils.logger import SystemLogger
from midastrader.structs.account import Account, EquityDetails
from midastrader.message_bus import MessageBus, EventType
from midastrader.core.adapters.performance.base import PerformanceManager
from midastrader.config import Parameters, Mode, LiveDataType
from midastrader.structs.trade import Trade
from midastrader.structs.events import (
    SignalEvent,
    TradeCommissionEvent,
    TradeEvent,
)
from midastrader.structs.orders import OrderType, Action
from midastrader.structs.signal import SignalInstruction
from midastrader.core.adapters.base_strategy import BaseStrategy
from midastrader.structs.constants import PRICE_FACTOR
from midastrader.structs.symbol import (
    Equity,
    Currency,
    Venue,
    Future,
    Industry,
    ContractUnits,
    SecurityType,
    FuturesMonth,
    TradingSession,
)


class TestStrategy(BaseStrategy):
    def primer(self):
        pass

    def prepare(self):
        pass

    def handle_event(self, event: MarketEvent) -> None:
        pass

    def get_strategy_data(self) -> pd.DataFrame:
        return pd.DataFrame()


class TestPerformanceManager(unittest.TestCase):
    def setUp(self) -> None:
        # Test symbols
        hogs = Future(
            instrument_id=1,
            broker_ticker="HEJ4",
            data_ticker="HE",
            midas_ticker="HE.n.0",
            security_type=SecurityType.FUTURE,
            fees=0.85,
            currency=Currency.USD,
            exchange=Venue.CME,
            initial_margin=4564.17,
            quantity_multiplier=40000,
            price_multiplier=0.01,
            product_code="HE",
            product_name="Lean Hogs",
            industry=Industry.AGRICULTURE,
            contract_size=40000,
            contract_units=ContractUnits.POUNDS,
            tick_size=0.00025,
            min_price_fluctuation=10,
            continuous=False,
            slippage_factor=10,
            lastTradeDateOrContractMonth="202404",
            trading_sessions=TradingSession(
                day_open=time(9, 0), day_close=time(14, 0)
            ),
            expr_months=[FuturesMonth.G, FuturesMonth.J, FuturesMonth.Z],
            term_day_rule="nth_business_day_10",
            market_calendar="CMEGlobex_Lean_Hog",
        )
        aapl = Equity(
            instrument_id=2,
            broker_ticker="AAPL",
            data_ticker="AAPL2",
            midas_ticker="AAPL",
            security_type=SecurityType.STOCK,
            currency=Currency.USD,
            exchange=Venue.NASDAQ,
            fees=0.1,
            initial_margin=0,
            quantity_multiplier=1,
            price_multiplier=1,
            company_name="Apple Inc.",
            industry=Industry.TECHNOLOGY,
            market_cap=10000000000.99,
            shares_outstanding=1937476363,
            slippage_factor=10,
            trading_sessions=TradingSession(
                day_open=time(9, 0), day_close=time(14, 0)
            ),
        )

        self.symbols_map = SymbolMap()
        self.symbols_map.add_symbol(hogs)
        self.symbols_map.add_symbol(aapl)

        # Parameters
        self.schema = mbn.Schema.OHLCV1_S
        self.stype = mbn.Stype.CONTINUOUS
        self.dataset = mbn.Dataset.FUTURES
        self.strategy_name = "Testing"
        self.capital = 1000000
        self.data_type = random.choice([LiveDataType.BAR, LiveDataType.TICK])
        self.strategy_allocation = 1.0
        self.start = "2020-05-18"
        self.end = "2023-12-31"

        self.params = Parameters(
            strategy_name=self.strategy_name,
            capital=self.capital,
            schema=self.schema,
            data_type=self.data_type,
            start=self.start,
            end=self.end,
            stype=self.stype,
            dataset=self.dataset,
            risk_free_rate=0.9,
            symbols=[hogs, aapl],
        )

        # Mock Logger
        logger = SystemLogger()
        logger.get_logger = MagicMock()

        # Portfolio server instance
        self.message_bus = MessageBus()
        self.manager = PerformanceManager(
            self.symbols_map,
            self.message_bus,
            self.params,
            Mode.BACKTEST,
            output_dir="",
        )

        self.manager.set_strategy(TestStrategy(Mock(), Mock()))
        threading.Thread(target=self.manager.process, daemon=True).start()

    # Basic Validation
    def test_handle_event_equity(self):
        equity_data = EquityDetails(
            timestamp=1709282000000000,
            equity_value=123456765432,
        )

        # Test
        self.message_bus.publish(EventType.EQUITY_UPDATE, equity_data)
        sleep(1)

        # Validate
        data = self.manager.equity_manager.equity_value
        self.assertEqual(data[-1], equity_data)

    def test_handle_event_account(self):
        # Account data
        account_data = Account(
            timestamp=16777700000000,
            full_available_funds=100000.0,
            full_init_margin_req=100000.0,
            net_liquidation=100000.0,
            unrealized_pnl=100000.0,
            full_maint_margin_req=100000.0,
            currency="USD",
        )

        # Test
        self.message_bus.publish(EventType.ACCOUNT_UPDATE_LOG, account_data)
        sleep(1)

        # Validate
        data = self.manager.account_manager.account_log
        self.assertEqual(data[-1], account_data)

    def test_handle_event_trade(self):
        # Trade data
        trade_id = "124243"
        trade_data = Trade(
            trade_id=1,
            leg_id=2,
            timestamp=16555000000000000,
            instrument=1,
            quantity=10.0,
            avg_price=85.98,
            trade_value=900.90,
            trade_cost=400.0,
            action=random.choice(["BUY", "SELL"]),
            fees=9.87,
        )

        trade_event = TradeEvent(trade_id, trade_data)

        # Test
        self.message_bus.publish(EventType.TRADE_UPDATE, trade_event)
        sleep(1)

        # Validate
        data = self.manager.trade_manager.trades[trade_id]
        self.assertEqual(data, trade_data)

    def test_handle_event_trade_commission(self):
        # Trade data
        trade_id = "124243"
        commission = 90.0
        trade_data = Trade(
            trade_id=1,
            leg_id=2,
            timestamp=16555000000000000,
            instrument=1,
            quantity=10.0,
            avg_price=85.98,
            trade_value=900.90,
            trade_cost=400.0,
            action=random.choice(["BUY", "SELL"]),
            fees=0.0,
        )
        trade_event = TradeEvent(trade_id, trade_data)
        self.message_bus.publish(EventType.TRADE_UPDATE, trade_event)
        sleep(1)

        # Test
        self.message_bus.publish(
            EventType.TRADE_UPDATE,
            TradeCommissionEvent(trade_id, commission),
        )
        sleep(1)

        # Validate
        data = self.manager.trade_manager.trades[trade_id]
        self.assertEqual(data.fees, commission)

    def test_handle_event_signal(self):
        # Signal data
        self.timestamp = 1651500000
        self.trade_capital = 1000090
        self.trade1 = SignalInstruction(
            instrument=1,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=5,
            weight=0.5,
            quantity=10.0,
        )
        self.trade2 = SignalInstruction(
            instrument=2,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=6,
            weight=0.5,
            quantity=10.0,
        )
        self.trade_instructions = [self.trade1, self.trade2]
        signal = SignalEvent(self.timestamp, self.trade_instructions)

        # Test
        self.message_bus.publish(EventType.SIGNAL_UPDATE, signal)
        sleep(1)

        # Validate
        data = self.manager.signal_manager.signals[-1]
        self.assertEqual(data, signal)

    def test_save_backtest(self):
        # Trades
        self.manager.trade_manager.trades = {
            "25432": Trade(
                timestamp=1640995200000000000,
                trade_id=1,
                leg_id=1,
                instrument=1,
                quantity=10.0,
                avg_price=10.0,
                trade_value=-100.0,
                trade_cost=100.0,
                fees=10.0,
                action=Action.LONG.value,
            ),
            "532": Trade(
                timestamp=1641081600000000000,
                trade_id=1,
                leg_id=1,
                instrument=1,
                quantity=-10.0,
                avg_price=15.0,
                trade_value=150.0,
                trade_cost=100.0,
                fees=10.0,
                action=Action.SELL.value,
            ),
            "5432": Trade(
                timestamp=1640995200000000000,
                trade_id=2,
                leg_id=1,
                instrument=1,
                quantity=-10.0,
                avg_price=20.0,
                trade_value=500.0,
                trade_cost=100.0,
                fees=10.0,
                action=Action.SHORT.value,
            ),
            "9867": Trade(
                timestamp=1641081600000000000,
                trade_id=2,
                leg_id=1,
                instrument=1,
                quantity=10.0,
                avg_price=18.0,
                trade_value=-180.0,
                trade_cost=100.0,
                fees=10.0,
                action=Action.COVER.value,
            ),
        }

        # Equity Curve
        self.manager.equity_manager.equity_value = [
            EquityDetails(timestamp=1641047400000000000, equity_value=1000.0),
            EquityDetails(timestamp=1641070800000000000, equity_value=1000.0),
            EquityDetails(timestamp=1641133800000000000, equity_value=1030.0),
            EquityDetails(timestamp=1641142800000000000, equity_value=1033.0),
            EquityDetails(timestamp=1641157200000000000, equity_value=1033.0),
            EquityDetails(timestamp=1641220200000000000, equity_value=1044.0),
            EquityDetails(timestamp=1641225600000000000, equity_value=1044.0),
            EquityDetails(timestamp=1641243600000000000, equity_value=1044.0),
        ]

        # Signals
        self.trade1 = SignalInstruction(
            instrument=1,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=5,
            weight=0.5,
            quantity=2.0,
        )
        self.trade2 = SignalInstruction(
            instrument=2,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=6,
            weight=0.5,
            quantity=2.0,
        )
        self.trade_instructions = [self.trade1, self.trade2]

        signal_event = SignalEvent(
            1717587686000000000,
            self.trade_instructions,
        )
        self.manager.signal_manager.update_signals(signal_event)

        # Test
        self.manager.save()
        backtest = self.manager.backtest

        # Validate parameters
        self.assertEqual(
            backtest.metadata.parameters.to_dict(),
            self.params.to_mbn().to_dict(),
        )

        # Validate static stats
        expected_static_keys = [
            "total_trades",
            "total_winning_trades",
            "total_losing_trades",
            "avg_profit",
            "avg_profit_percent",
            "avg_gain",
            "avg_gain_percent",
            "avg_loss",
            "avg_loss_percent",
            "profitability_ratio",
            "profit_factor",
            "profit_and_loss_ratio",
            "total_fees",
            "net_profit",
            "beginning_equity",
            "ending_equity",
            "total_return",
            "annualized_return",
            "daily_standard_deviation_percentage",
            "annual_standard_deviation_percentage",
            "max_drawdown_percentage_period",
            "max_drawdown_percentage_daily",
            "sharpe_ratio",
            "sortino_ratio",
        ]

        static_stats = list(backtest.metadata.static_stats.to_dict().keys())

        for key in static_stats:
            self.assertIn(key, expected_static_keys)
            self.assertIsNotNone(backtest.metadata.static_stats.to_dict()[key])

        # Validate timeseries stats
        expected_timeseries_keys = {
            "timestamp",
            "equity_value",
            "period_return",
            "cumulative_return",
            "percent_drawdown",
        }
        actual_daily_timeseries_keys = set(
            backtest.daily_timeseries_stats[0].to_dict().keys()
        )
        actual_period_timeseries_keys = set(
            backtest.period_timeseries_stats[0].to_dict().keys()
        )

        self.assertEqual(
            actual_daily_timeseries_keys,
            expected_timeseries_keys,
            "Timeseries stats keys do not match expected keys.",
        )
        self.assertEqual(
            actual_period_timeseries_keys,
            expected_timeseries_keys,
            "Timeseries stats keys do not match expected keys.",
        )

    def test_save_live(self):
        # Portfolio server instance
        self.message_bus = MessageBus()
        self.manager = PerformanceManager(
            self.symbols_map,
            self.message_bus,
            self.params,
            Mode.LIVE,
            output_dir="",
        )

        self.manager.set_strategy(TestStrategy(Mock(), Mock()))
        threading.Thread(target=self.manager.process, daemon=True).start()

        # Signals
        self.trade1 = SignalInstruction(
            instrument=1,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=5,
            weight=0.5,
            quantity=2.0,
        )
        self.trade2 = SignalInstruction(
            instrument=2,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=6,
            weight=0.5,
            quantity=2.0,
        )
        self.trade_instructions = [self.trade1, self.trade2]

        signal_event = SignalEvent(
            1717587686000000000,
            self.trade_instructions,
        )
        self.manager.signal_manager.update_signals(signal_event)

        # Trades
        trades = {
            "25432": Trade(
                timestamp=1640995200000000000,
                trade_id=1,
                leg_id=1,
                instrument=1,
                quantity=10.0,
                avg_price=10.0,
                trade_value=-100.0,
                trade_cost=100.0,
                fees=100.0,
                action=Action.LONG.value,
            ),
            "532": Trade(
                timestamp=1641081600000000000,
                trade_id=1,
                leg_id=1,
                instrument=1,
                quantity=-10.0,
                avg_price=15.0,
                trade_value=150.0,
                trade_cost=100.0,
                fees=10.0,
                action=Action.SELL.value,
            ),
            "5432": Trade(
                timestamp=1640995200000000000,
                trade_id=2,
                leg_id=1,
                instrument=1,
                quantity=-10.0,
                avg_price=20.0,
                trade_value=500.0,
                trade_cost=100.0,
                fees=10.0,
                action=Action.SHORT.value,
            ),
            "9867": Trade(
                timestamp=1641081600000000000,
                trade_id=2,
                leg_id=1,
                instrument=1,
                quantity=10.0,
                avg_price=18.0,
                trade_value=-180.0,
                trade_cost=100.0,
                fees=10.0,
                action=Action.COVER.value,
            ),
        }

        self.manager.trade_manager.trades = trades

        # Account
        self.manager.account_manager.account_log = [
            Account(
                buying_power=2563178.43,
                currency="USD",
                excess_liquidity=768953.53,
                full_available_funds=768953.53,
                full_init_margin_req=263.95,
                full_maint_margin_req=263.95,
                futures_pnl=-367.5,
                net_liquidation=769217.48,
                total_cash_balance=-10557.9223,
                unrealized_pnl=0.0,
                timestamp=165000000000,
            ),
            Account(
                buying_power=2541533.29,
                currency="USD",
                excess_liquidity=763767.68,
                full_available_funds=762459.99,
                full_init_margin_req=6802.69,
                full_maint_margin_req=5495.0,
                futures_pnl=-373.3,
                net_liquidation=769262.67,
                total_cash_balance=768538.5532,
                unrealized_pnl=-11.73,
                timestamp=166000000000,
            ),
        ]

        # Test
        self.manager.save()
        live_summary = self.manager.live_summary

        # Validate account
        expected_account = mbn.AccountSummary(
            start_timestamp=165000000000,
            start_full_available_funds=int(768953.53 * PRICE_FACTOR),
            start_full_init_margin_req=int(263.95 * PRICE_FACTOR),
            start_net_liquidation=int(769217.48 * PRICE_FACTOR),
            start_buying_power=int(2563178.43 * PRICE_FACTOR),
            start_unrealized_pnl=int(0.00 * PRICE_FACTOR),
            start_full_maint_margin_req=int(263.95 * PRICE_FACTOR),
            start_excess_liquidity=int(768953.53 * PRICE_FACTOR),
            start_futures_pnl=int(-367.50 * PRICE_FACTOR),
            start_total_cash_balance=int(-10557.9223 * PRICE_FACTOR),
            end_timestamp=166000000000,
            end_full_available_funds=int(762459.99 * PRICE_FACTOR),
            end_full_init_margin_req=int(6802.69 * PRICE_FACTOR),
            end_net_liquidation=int(769262.67 * PRICE_FACTOR),
            end_unrealized_pnl=int(-11.73 * PRICE_FACTOR),
            end_full_maint_margin_req=int(5495.00 * PRICE_FACTOR),
            end_excess_liquidity=int(763767.68 * PRICE_FACTOR),
            end_buying_power=int(2541533.29 * PRICE_FACTOR),
            end_futures_pnl=int(-373.30 * PRICE_FACTOR),
            end_total_cash_balance=int(768538.5532 * PRICE_FACTOR),
            currency="USD",
        )

        self.assertEqual(
            live_summary.account.to_dict(), expected_account.to_dict()
        )


if __name__ == "__main__":
    unittest.main()

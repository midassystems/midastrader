import unittest
import numpy as np
import pandas as pd
from unittest.mock import Mock

from midas.structs.orders import Action, OrderType
from midas.structs.signal import SignalInstruction
from midas.structs.trade import Trade
from midas.structs.account import Account
from midas.structs.events import SignalEvent
from midas.core.performance.managers import (
    TradeManager,
    SignalManager,
    EquityManager,
    AccountManager,
)


class TestTradeManager(unittest.TestCase):
    def setUp(self):
        self.manager = TradeManager(Mock())
        self.manager.trades = {
            "1234": Trade(
                timestamp=1712066400000000000,
                trade_id=13,
                leg_id=1,
                instrument=43,
                quantity=-63,
                avg_price=104.425,
                trade_value=-2631510.0,
                trade_cost=354511.71,
                action="SHORT",
                fees=-53.55,
            ),
            "10928": Trade(
                timestamp=1712066400000000000,
                trade_id=13,
                leg_id=2,
                instrument=70,
                quantity=114,
                avg_price=431.5,
                trade_value=2459550.0,
                trade_cost=236591.04,
                action="LONG",
                fees=-96.9,
            ),
            "2827": Trade(
                timestamp=1712235600000000000,
                trade_id=13,
                leg_id=1,
                instrument=43,
                quantity=63,
                avg_price=104.55,
                trade_value=2634660.0,
                trade_cost=354511.71,
                action="COVER",
                fees=-53.55,
            ),
            "32342": Trade(
                timestamp=1712235600000000000,
                trade_id=13,
                leg_id=2,
                instrument=70,
                quantity=-114,
                avg_price=433.0,
                trade_value=-2468100.0,
                trade_cost=236591.04,
                action="SELL",
                fees=-96.9,
            ),
            "23232": Trade(
                timestamp=1712336400000000000,
                trade_id=14,
                leg_id=1,
                instrument=43,
                quantity=-63,
                avg_price=107.925,
                trade_value=-2719710.0,
                trade_cost=354511.71,
                action="SHORT",
                fees=-53.55,
            ),
            "23234234": Trade(
                timestamp=1712336400000000000,
                trade_id=14,
                leg_id=2,
                instrument=70,
                quantity=114,
                avg_price=433.25,
                trade_value=2469525.0,
                trade_cost=236591.04,
                action="LONG",
                fees=-96.9,
            ),
            "234342": Trade(
                timestamp=1712754000000000000,
                trade_id=14,
                leg_id=1,
                instrument=43,
                quantity=63,
                avg_price=107.875,
                trade_value=2718450.0,
                trade_cost=354511.71,
                action="COVER",
                fees=-53.55,
            ),
            "9434": Trade(
                timestamp=1712754000000000000,
                trade_id=14,
                leg_id=2,
                instrument=70,
                quantity=-114,
                avg_price=433.5,
                trade_value=-2470950.0,
                trade_cost=236591.04,
                action="SELL",
                fees=-96.9,
            ),
            "087342": Trade(
                timestamp=1712926800000000000,
                trade_id=15,
                leg_id=1,
                instrument=43,
                quantity=63,
                avg_price=105.25,
                trade_value=2652300.0,
                trade_cost=354511.71,
                action="LONG",
                fees=-53.55,
            ),
            "635209": Trade(
                timestamp=1712926800000000000,
                trade_id=15,
                leg_id=2,
                instrument=70,
                quantity=-115,
                avg_price=446.25,
                trade_value=-2565937.5,
                trade_cost=238666.4,
                action="SHORT",
                fees=-97.75,
            ),
            "9654": Trade(
                timestamp=1713272400000000000,
                trade_id=15,
                leg_id=1,
                instrument=43,
                quantity=-63,
                avg_price=102.775,
                trade_value=-2589930.0,
                trade_cost=354511.71,
                action="SELL",
                fees=-53.55,
            ),
            "5498703": Trade(
                timestamp=1713272400000000000,
                trade_id=15,
                leg_id=2,
                instrument=70,
                quantity=115,
                avg_price=441.75,
                trade_value=2540062.5,
                trade_cost=238666.4,
                action="COVER",
                fees=-97.75,
            ),
        }

        self.pnl = np.array(
            [
                13466.7,
                -63784.2,
                103997.8,
                -83166.9,
                63782.7,
                7025.7,
                -16613.5,
                531.6,
                31406.6,
                53848.1,
                48177.8,
                29275.1,
                5099.1,
                2384.1,
                -36797.6,
                28295.1,
            ]
        )

    def test_aggregate_trades(self):
        # Test
        aggregated_df = self.manager._aggregate_trades()

        # Expected
        data = {
            "trade_id": [13, 14, 15],
            "start_date": [
                1712066400000000000,
                1712336400000000000,
                1712926800000000000,
            ],
            "end_date": [
                1712235600000000000,
                1712754000000000000,
                1713272400000000000,
            ],
            "entry_value": [-171960.0, -250185.0, 86362.5],
            "exit_value": [166560.0, 247500.0, -49867.5],
            "entry_cost": [591102.75, 591102.75, 593178.11],
            "exit_cost": [591102.75, 591102.75, 593178.11],
            "fees": [-300.9, -300.9, -302.6],
            "gain/loss": [5400.0, 2685.0, -36495.0],
            "pnl": [5099.1, 2384.1, -36797.6],
            "pnl_percentage": [0.00862642, 0.00403331, -0.06203465599902194],
        }
        expected_df = pd.DataFrame(data)

        # Validate
        pd.testing.assert_frame_equal(aggregated_df, expected_df)

    def test_calculate_statistics(self):
        # Test
        result = self.manager.calculate_trade_statistics()

        # Expected
        keys = [
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
        ]

        # Validate
        for key in keys:
            self.assertIsNotNone(result[key])

    def test_total_trades(self):
        expected_total_trades = 16

        # Test
        total_trades = self.manager.total_trades(self.pnl)

        # Validate
        self.assertEqual(total_trades, expected_total_trades)

    # Total Winning Trades
    def test_total_winning_trades(self):
        expected_winning_trades = 12

        # Test
        total_winning_trades = self.manager.total_winning_trades(self.pnl)

        # Validate
        self.assertEqual(total_winning_trades, expected_winning_trades)

    # Total Losing Trades
    def test_total_losing_trades(self):
        expected_losing_trades = 4

        # Test
        total_losing_trades = self.manager.total_losing_trades(self.pnl)

        # Validate
        self.assertEqual(total_losing_trades, expected_losing_trades)

    # Total Avg Win Percent
    def test_avg_win_return_rate(self):
        expected_avg_win = 32274.20

        # Test
        avg_win_return_rate = self.manager.avg_gain(self.pnl)

        # Validate
        self.assertAlmostEqual(avg_win_return_rate, expected_avg_win, places=4)

    # Total avg_loss_return_rate
    def test_avg_loss_return_rate(self):
        expected_avg_loss = -50090.55

        # Test
        avg_loss_return_rate = self.manager.avg_loss(self.pnl)

        # Validate
        self.assertAlmostEqual(
            avg_loss_return_rate, expected_avg_loss, places=4
        )

    # Percent Profitable
    def test_profitability_ratio(self):
        expected_profitability_ratio = 12 / 16

        # Test
        profitability_ratio = self.manager.profitability_ratio(self.pnl)

        # Validate
        self.assertEqual(profitability_ratio, expected_profitability_ratio)

    # Avg Trade Profit
    def test_avg_trade_profit(self):
        expected_avg_trade_profit = 11683.0125

        # Test
        average_trade_profit = self.manager.avg_profit(self.pnl)

        # Validate
        self.assertEqual(average_trade_profit, expected_avg_trade_profit)

    # Profit Factor
    def test_profit_factor(self):
        expected_profit_factor = 1.933

        # Test
        profit_factor = self.manager.profit_factor(self.pnl)

        # Validate
        self.assertEqual(profit_factor, expected_profit_factor)

    # Profit & Loss Ratio
    def test_profit_and_loss_ratio(self):
        expected_pnl_ratio = 0.6443

        # Test
        profit_and_loss_ratio = self.manager.profit_and_loss_ratio(self.pnl)

        # Validate
        self.assertEqual(profit_and_loss_ratio, expected_pnl_ratio)


class TestEquityManager(unittest.TestCase):
    def setUp(self):
        self.manager = EquityManager(Mock())
        self.manager.equity_value = [
            {"timestamp": 1713888000000000000, "equity_value": 1189792.75},
            {"timestamp": 1713891600000000000, "equity_value": 1193107.75},
            {"timestamp": 1713895200000000000, "equity_value": 1192942.75},
            {"timestamp": 1713963600000000000, "equity_value": 1198612.75},
            {"timestamp": 1713967200000000000, "equity_value": 1179022.75},
            {"timestamp": 1713970800000000000, "equity_value": 1182667.75},
            {"timestamp": 1713974400000000000, "equity_value": 1185022.75},
            {"timestamp": 1713978000000000000, "equity_value": 1175647.75},
            {"timestamp": 1713981600000000000, "equity_value": 1174552.75},
            {"timestamp": 1714050000000000000, "equity_value": 1242757.75},
            {"timestamp": 1714050000000000000, "equity_value": 1242607.3},
            {"timestamp": 1714053600000000000, "equity_value": 1242607.3},
            {"timestamp": 1714057200000000000, "equity_value": 1242607.3},
            {"timestamp": 1714060800000000000, "equity_value": 1242607.3},
        ]
        self.raw_equity_df = pd.DataFrame(self.manager.equity_value)
        self.raw_equity_df.set_index("timestamp", inplace=True)

    def test_calculate_return_and_drawdown(self):
        # Test
        result = self.manager._calculate_return_and_drawdown(
            self.raw_equity_df
        )

        # Expected
        data = {
            "timestamp": [
                1713888000000000000,
                1713891600000000000,
                1713895200000000000,
                1713963600000000000,
                1713967200000000000,
                1713970800000000000,
                1713974400000000000,
                1713978000000000000,
                1713981600000000000,
                1714050000000000000,
                1714050000000000000,
                1714053600000000000,
                1714057200000000000,
                1714060800000000000,
            ],
            "equity_value": [
                1189792.75,
                1193107.75,
                1192942.75,
                1198612.75,
                1179022.75,
                1182667.75,
                1185022.75,
                1175647.75,
                1174552.75,
                1242757.75,
                1242607.30,
                1242607.30,
                1242607.30,
                1242607.30,
            ],
            "period_return": [
                0.000000,
                0.002786,
                -0.000138,
                0.004753,
                -0.016344,
                0.003092,
                0.001991,
                -0.007911,
                -0.000931,
                0.058069,
                -0.000121,
                0.000000,
                0.000000,
                0.000000,
            ],
            "cumulative_return": [
                0.000000,
                0.002786,
                0.002648,
                0.007413,
                -0.009052,
                -0.005988,
                -0.004009,
                -0.011889,
                -0.012809,
                0.044516,
                0.044390,
                0.044390,
                0.044390,
                0.044390,
            ],
            "percent_drawdown": [
                0.0,
                0.0,
                -0.000138,
                0.0,
                -0.016344,
                -0.013303,
                -0.011338,
                -0.019159,
                -0.020072,
                0.0,
                -0.000121,
                -0.000121,
                -0.000121,
                -0.000121,
            ],
        }
        expected_df = pd.DataFrame(data)
        expected_df.set_index("timestamp", inplace=True)

        # Validate
        pd.testing.assert_frame_equal(result, expected_df)

    def test_calculate_statistics(self):
        # Test
        result = self.manager.calculate_equity_statistics()

        # Expected
        keys = [
            "net_profit",
            "beginning_equity",
            "ending_equity",
            "total_return",
            "daily_standard_deviation_percentage",
            "annual_standard_deviation_percentage",
            "max_drawdown_percentage_period",
            "max_drawdown_percentage_daily",
            "sharpe_ratio",
            "sortino_ratio",
        ]

        # Validate
        for key in keys:
            self.assertIsNotNone(result[key])


class TestAccountManager(unittest.TestCase):
    def setUp(self):
        self.manager = AccountManager(Mock())

    def test_account_log(self):
        account_info = Account(
            timestamp=1650000000,
            full_available_funds=100000.0,
            full_init_margin_req=100000.0,
            net_liquidation=100000.0,
            unrealized_pnl=100000.0,
            full_maint_margin_req=100000.0,
            currency="USD",
        )

        # Test
        self.manager.update_account_log(account_info)

        # Validate
        self.assertEqual(self.manager.account_log[0], account_info)


class TestSignalManager(unittest.TestCase):
    def setUp(self):
        self.manager = SignalManager(Mock())

        # Signal data
        self.timestamp = 1651500000
        self.trade1 = SignalInstruction(
            instrument=1,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=5,
            weight=0.5,
            quantity=10,
        )
        self.trade2 = SignalInstruction(
            instrument=2,
            order_type=OrderType.MARKET,
            action=Action.LONG,
            trade_id=2,
            leg_id=6,
            weight=0.5,
            quantity=10,
        )
        self.trade_instructions = [self.trade1, self.trade2]
        self.event = SignalEvent(self.timestamp, self.trade_instructions)
        self.manager.update_signals(self.event)

    def test_flatten_trade_instructions(self):
        flatten_dict = [
            {
                "timestamp": 1651500000,
                "ticker": 1,
                "order_type": "MKT",
                "action": "LONG",
                "trade_id": 2,
                "leg_id": 5,
                "weight": 0.5,
                "quantity": 10,
                "limit_price": "",
                "aux_price": "",
            },
            {
                "timestamp": 1651500000,
                "ticker": 2,
                "order_type": "MKT",
                "action": "LONG",
                "trade_id": 2,
                "leg_id": 6,
                "weight": 0.5,
                "quantity": 10,
                "limit_price": "",
                "aux_price": "",
            },
        ]
        flattened_df = pd.DataFrame(flatten_dict)

        # Test
        df = self.manager._flatten_trade_instructions()

        # Validate
        pd.testing.assert_frame_equal(df, flattened_df)

import unittest
from midas.backtest import Backtest


class TestBacktest(unittest.TestCase):
    def setUp(self) -> None:
        # Mock backtest data
        self.parameters = {
            "strategy_name": "cointegrationzscore",
            "capital": 100000,
            "data_type": "BAR",
            "train_start": "2018-05-18",
            "train_end": "2023-01-19",
            "test_start": "2023-01-19",
            "test_end": "2024-01-19",
            "tickers": ["AAPL"],
            "benchmark": ["^GSPC"],
        }
        self.static_stats = {
            "net_profit": 330.0,
            "total_fees": 40.0,
            "total_return": 0.33,
            "ending_equity": 1330.0,
            "max_drawdown": 0.0,
            "total_trades": 2,
            "num_winning_trades": 2,
            "num_lossing_trades": 0,
            "avg_win_percent": 0.45,
            "avg_loss_percent": 0,
            "percent_profitable": 1.0,
            "profit_and_loss": 0.0,
            "profit_factor": 0.0,
            "avg_trade_profit": 165.0,
            "sortino_ratio": 0.0,
        }

        self.timeseries_stats = [
            {
                "timestamp": "2023-12-09T12:00:00Z",
                "equity_value": 10000.0,
                "percent_drawdown": 9.9,
                "cumulative_return": -0.09,
                "period_return": 79.9,
                "daily_strategy_return": "0.330",
                "daily_benchmark_return": "0.00499",
            },
            {
                "timestamp": "2023-12-10T12:00:00Z",
                "equity_value": 10000.0,
                "percent_drawdown": 9.9,
                "cumulative_return": -0.09,
                "period_return": 79.9,
                "daily_strategy_return": "0.087",
                "daily_benchmark_return": "0.009",
            },
        ]
        self.trades = [
            {
                "trade_id": 1,
                "leg_id": 1,
                "timestamp": "2023-01-03T00:00:00+0000",
                "ticker": "AAPL",
                "quantity": 4,
                "price": 130.74,
                "cost": -522.96,
                "action": "BUY",
                "fees": 0.0,
            }
        ]
        self.signals = [
            {
                "timestamp": "2023-01-03T00:00:00+0000",
                "trade_instructions": [
                    {
                        "ticker": "AAPL",
                        "action": "BUY",
                        "trade_id": 1,
                        "leg_id": 1,
                        "weight": 0.05,
                    },
                    {
                        "ticker": "MSFT",
                        "action": "SELL",
                        "trade_id": 1,
                        "leg_id": 2,
                        "weight": 0.05,
                    },
                ],
            }
        ]

        # Create backtest object
        self.backtest_obj = Backtest(
            name="testing123",
            parameters=self.parameters,
            static_stats=self.static_stats,
            period_timeseries_stats=self.timeseries_stats,
            daily_timeseries_stats=self.timeseries_stats,
            trade_data=self.trades,
            signal_data=self.signals,
        )

    def test_to_dict(self):
        # Test
        backtest_dict = self.backtest_obj.to_dict()

        # Validate
        self.assertEqual(backtest_dict["parameters"], self.parameters)
        self.assertEqual(backtest_dict["static_stats"], self.static_stats)
        self.assertEqual(
            backtest_dict["period_timeseries_stats"], self.timeseries_stats
        )
        self.assertEqual(
            backtest_dict["daily_timeseries_stats"], self.timeseries_stats
        )
        self.assertEqual(backtest_dict["signals"], self.signals)
        self.assertEqual(backtest_dict["trades"], self.trades)

    def test_type_constraints(self):
        with self.assertRaisesRegex(
            ValueError, "'parameters' field must be a dictionary."
        ):
            Backtest(
                name="testing1234",
                parameters="self.parameters,",
                static_stats=self.static_stats,
                period_timeseries_stats=self.timeseries_stats,
                daily_timeseries_stats=self.timeseries_stats,
                trade_data=self.trades,
                signal_data=self.signals,
            )

        with self.assertRaisesRegex(
            ValueError, "'static_stats' field must be a dictionaries."
        ):
            Backtest(
                name="testing1234",
                parameters=self.parameters,
                static_stats="self.static_stats",
                period_timeseries_stats=self.timeseries_stats,
                daily_timeseries_stats=self.timeseries_stats,
                trade_data=self.trades,
                signal_data=self.signals,
            )

        with self.assertRaisesRegex(
            ValueError,
            "'period_timeseries_stats' field must be a list of dictionaries.",
        ):
            Backtest(
                name="testing2e233",
                parameters=self.parameters,
                static_stats=self.static_stats,
                period_timeseries_stats="self.timeseries_stats,",
                daily_timeseries_stats=self.timeseries_stats,
                trade_data=self.trades,
                signal_data=self.signals,
            )

        with self.assertRaisesRegex(
            ValueError,
            "'daily_timeseries_stats' field must be a list of dictionaries.",
        ):
            Backtest(
                name="testing1234",
                parameters=self.parameters,
                static_stats=self.static_stats,
                period_timeseries_stats=self.timeseries_stats,
                daily_timeseries_stats="self.timeseries_stats",
                trade_data=self.trades,
                signal_data=self.signals,
            )

        with self.assertRaisesRegex(
            ValueError, "'trade_data' field must be a list of dictionaries."
        ):
            Backtest(
                name="testing1234",
                parameters=self.parameters,
                static_stats=self.static_stats,
                period_timeseries_stats=self.timeseries_stats,
                daily_timeseries_stats=self.timeseries_stats,
                trade_data="self.trades",
                signal_data=self.signals,
            )

        with self.assertRaisesRegex(
            ValueError, "'signal_data' field must be a list of dictionaries."
        ):
            Backtest(
                name="testing1234",
                parameters=self.parameters,
                static_stats=self.static_stats,
                period_timeseries_stats=self.timeseries_stats,
                daily_timeseries_stats=self.timeseries_stats,
                trade_data=self.trades,
                signal_data="self.signals",
            )


if __name__ == "__main__":
    unittest.main()

import random
import unittest
from datetime import datetime, time

from midastrader.utils.unix import iso_to_unix
from midastrader.config import Parameters, LiveDataType, Config
from midastrader.structs.symbol import (
    Future,
    Currency,
    ContractUnits,
    Venue,
    FuturesMonth,
    TradingSession,
    SecurityType,
    Industry,
)


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_from_toml(self):
        # Test
        config = Config.from_toml("tests/unit/config.toml")

        # Validate
        self.assertTrue(config.general != {})
        self.assertTrue(config.strategy != {})
        self.assertTrue(config.risk != {})
        self.assertTrue(config.executors != {})
        self.assertTrue(config.vendors != {})


class TestParameters(unittest.TestCase):
    def setUp(self) -> None:
        # Test parameter data
        self.schema = "Ohlcv-1s"
        self.strategy_name = "Testing"
        self.capital = 1000000
        self.data_type = random.choice([LiveDataType.BAR, LiveDataType.TICK])
        self.strategy_allocation = 1.0
        self.start = "2020-05-18"
        self.end = "2023-12-31"
        self.symbols = [
            Future(
                instrument_id=1,
                broker_ticker="HEJ4",
                data_ticker="HE",
                midas_ticker="HE.n.0",
                security_type=SecurityType.FUTURE,
                currency=Currency.USD,
                exchange=Venue.CME,
                fees=0.85,
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
                lastTradeDateOrContractMonth="202404",
                slippage_factor=10,
                trading_sessions=TradingSession(
                    day_open=time(9, 0), day_close=time(14, 0)
                ),
                expr_months=[FuturesMonth.G, FuturesMonth.J, FuturesMonth.Z],
                term_day_rule="nth_business_day_10",
                market_calendar="CMEGlobex_Lean_Hog",
            ),
            Future(
                instrument_id=2,
                broker_ticker="ZCJ4",
                data_ticker="ZC",
                midas_ticker="ZC.n.0",
                security_type=SecurityType.FUTURE,
                currency=Currency.USD,
                exchange=Venue.CBOT,
                fees=0.85,
                initial_margin=2056.75,
                quantity_multiplier=40000,
                price_multiplier=0.01,
                product_code="ZC",
                product_name="Corn",
                industry=Industry.AGRICULTURE,
                contract_size=5000,
                contract_units=ContractUnits.BUSHELS,
                tick_size=0.0025,
                min_price_fluctuation=10,
                continuous=False,
                lastTradeDateOrContractMonth="202406",
                slippage_factor=10,
                trading_sessions=TradingSession(
                    day_open=time(9, 0), day_close=time(14, 0)
                ),
                expr_months=[FuturesMonth.G, FuturesMonth.J, FuturesMonth.Z],
                term_day_rule="nth_business_day_10",
                market_calendar="CMEGlobex_Lean_Grain",
            ),
        ]

    # Basic Validation
    def test_construction(self):
        # Test
        params = Parameters(
            strategy_name=self.strategy_name,
            capital=self.capital,
            schema=self.schema,
            data_type=self.data_type,
            start=self.start,
            end=self.end,
            risk_free_rate=0.9,
            symbols=self.symbols,
        )
        # Validate
        self.assertEqual(params.strategy_name, self.strategy_name)
        self.assertEqual(params.capital, self.capital)
        self.assertEqual(params.data_type, self.data_type)
        self.assertEqual(params.start, self.start)
        self.assertEqual(params.end, self.end)
        self.assertEqual(params.symbols, self.symbols)
        self.assertEqual(params.tickers, ["HE.n.0", "ZC.n.0"])

    def test_to_dict(self):
        params = Parameters(
            strategy_name=self.strategy_name,
            capital=self.capital,
            schema=self.schema,
            data_type=self.data_type,
            start=self.start,
            end=self.end,
            risk_free_rate=0.9,
            symbols=self.symbols,
        )
        # Test
        params_dict = params.to_dict()

        # Validate
        self.assertEqual(params_dict["strategy_name"], self.strategy_name)
        self.assertEqual(params_dict["capital"], self.capital)
        self.assertEqual(params_dict["schema"], self.schema)

        self.assertEqual(params_dict["data_type"], self.data_type.value)
        self.assertEqual(params_dict["start"], iso_to_unix(self.start))
        self.assertEqual(params_dict["end"], iso_to_unix(self.end))
        self.assertEqual(params_dict["tickers"], ["HE.n.0", "ZC.n.0"])

    def test_from_dict(self):
        mock_dict = {
            "strategy_name": "TestStrategy",
            "schema": "Ohlcv-1s",
            "start": "2020-01-01",
            "end": "2023-01-01",
            "capital": 1000000,
            "data_type": "BAR",
            "risk_free_rate": 0.5,
            "symbols": [
                {
                    "type": "Future",
                    "instrument_id": 1,
                    "broker_ticker": "HEJ4",
                    "data_ticker": "HE",
                    "midas_ticker": "HE.n.0",
                    "security_type": "FUTURE",
                    "currency": "USD",
                    "exchange": "CME",
                    "fees": 0.85,
                    "initial_margin": 5627.17,
                    "quantity_multiplier": 40000,
                    "price_multiplier": 0.01,
                    "product_code": "HE",
                    "product_name": "Lean Hogs",
                    "industry": "AGRICULTURE",
                    "contract_size": 40000,
                    "contract_units": "POUNDS",
                    "tick_size": 0.00025,
                    "min_price_fluctuation": 10.0,
                    "continuous": True,
                    "lastTradeDateOrContractMonth": "202404",
                    "slippage_factor": 0,
                    "trading_sessions": {
                        "day_open": "09:30",
                        "day_close": "14:05",
                    },
                    "expr_months": ["G", "J", "K", "M", "N", "Q", "V", "Z"],
                    "term_day_rule": "nth_business_day_10",
                    "market_calendar": "CMEGlobex_Lean_Hog",
                },
                {
                    "type": "Future",
                    "instrument_id": 70,
                    "broker_ticker": "ZC",
                    "data_ticker": "ZC",
                    "midas_ticker": "ZC.n.0",
                    "security_type": "FUTURE",
                    "currency": "USD",
                    "exchange": "CBOT",
                    "fees": 0.85,
                    "initial_margin": 2075.36,
                    "quantity_multiplier": 5000,
                    "price_multiplier": 0.01,
                    "product_code": "ZC",
                    "product_name": "Corn",
                    "industry": "AGRICULTURE",
                    "contract_size": 5000,
                    "contract_units": "BUSHELS",
                    "tick_size": 0.0025,
                    "min_price_fluctuation": 12.50,
                    "continuous": True,
                    "lastTradeDateOrContractMonth": "202404",
                    "slippage_factor": 0,
                    "trading_sessions": {
                        "day_open": "09:30",
                        "day_close": "14:20",
                        "night_open": "20:00",
                        "night_close": "08:45",
                    },
                    "expr_months": ["H", "K", "N", "U", "Z"],
                    "term_day_rule": "nth_bday_before_nth_day_1_15",
                    "market_calendar": "CMEGlobex_Grains",
                },
            ],
        }

        # Test
        params = Parameters.from_dict(mock_dict)

        # Validate
        self.assertEqual(params.strategy_name, "TestStrategy")
        self.assertEqual(params.capital, 1000000)
        self.assertEqual(params.risk_free_rate, 0.5)
        self.assertEqual(params.data_type, LiveDataType.BAR)
        self.assertEqual(params.start, "2020-01-01")
        self.assertEqual(params.end, "2023-01-01")

        # Validate symbols
        self.assertEqual(len(params.symbols), 2)
        self.assertIsInstance(params.symbols[0], Future)
        self.assertIsInstance(params.symbols[1], Future)
        self.assertEqual(params.symbols[0].broker_ticker, "HEJ4")
        self.assertEqual(params.symbols[1].broker_ticker, "ZC")

    # Type Validation
    def test_type_errors(self):
        with self.assertRaisesRegex(
            TypeError, "'strategy_name' must be of type str."
        ):
            Parameters(
                schema=self.schema,
                strategy_name=123,
                capital=self.capital,
                data_type=self.data_type,
                start=self.start,
                end=self.end,
                symbols=self.symbols,
            )

        with self.assertRaisesRegex(
            TypeError, "'capital' must be of type int."
        ):
            Parameters(
                schema=self.schema,
                strategy_name=self.strategy_name,
                capital="1000",
                data_type=self.data_type,
                start=self.start,
                end=self.end,
                symbols=self.symbols,
            )

        with self.assertRaisesRegex(
            TypeError,
            "'data_type' must be of type LiveDataType.",
        ):
            Parameters(
                schema=self.schema,
                strategy_name=self.strategy_name,
                capital=self.capital,
                data_type="BAR",
                start=self.start,
                end=self.end,
                symbols=self.symbols,
            )

        with self.assertRaisesRegex(TypeError, "'start' must be of type str."):
            Parameters(
                schema=self.schema,
                strategy_name=self.strategy_name,
                capital=self.capital,
                data_type=self.data_type,
                start=datetime(2020, 10, 10),
                end=self.end,
                symbols=self.symbols,
            )

        with self.assertRaisesRegex(TypeError, "'end' must be of type str."):
            Parameters(
                schema=self.schema,
                strategy_name=self.strategy_name,
                capital=self.capital,
                data_type=self.data_type,
                start=self.start,
                end=datetime(2020, 10, 10),
                symbols=self.symbols,
            )

        with self.assertRaisesRegex(
            TypeError, "'symbols' must be of type list."
        ):
            Parameters(
                schema=self.schema,
                strategy_name=self.strategy_name,
                capital=self.capital,
                data_type=self.data_type,
                start=self.start,
                end=self.end,
                symbols="tests",
            )

        with self.assertRaisesRegex(
            TypeError,
            "All 'symbols' must be instances of Symbol",
        ):
            Parameters(
                schema=self.schema,
                strategy_name=self.strategy_name,
                capital=self.capital,
                data_type=self.data_type,
                start=self.start,
                end=self.end,
                symbols=["appl", "tsla"],
            )

    # Constraint Validation
    def test_value_constraints(self):
        with self.assertRaisesRegex(
            ValueError, "'capital' must be greater than zero."
        ):
            Parameters(
                schema=self.schema,
                strategy_name=self.strategy_name,
                capital=-1,
                data_type=self.data_type,
                start=self.start,
                end=self.end,
                symbols=self.symbols,
            )


if __name__ == "__main__":
    unittest.main()

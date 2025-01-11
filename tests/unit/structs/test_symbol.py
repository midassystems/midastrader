import unittest
import pandas as pd
from datetime import time
from ibapi.contract import Contract

from midastrader.structs import (
    Action,
    SecurityType,
    Venue,
    Equity,
    SymbolMap,
    SymbolFactory,
    Future,
    TradingSession,
    Currency,
    Industry,
    Option,
    FuturesMonth,
    Right,
    ContractUnits,
)


class TestEquity(unittest.TestCase):
    def setUp(self) -> None:
        # Mock equity data
        self.instrument_id = 1
        self.broker_ticker = "AAPL"
        self.data_ticker = "AAPL2"
        self.midas_ticker = "AAPL"
        self.security_type = SecurityType.STOCK
        self.currency = Currency.USD
        self.exchange = Venue.NASDAQ
        self.fees = 0.1
        self.initial_margin = 0
        self.quantity_multiplier = 1
        self.price_multiplier = 1
        self.company_name = "Apple Inc."
        self.industry = Industry.TECHNOLOGY
        self.market_cap = 10000000000.99
        self.shares_outstanding = 1937476363
        self.slippage_factor = 10
        self.trading_sessions = TradingSession(
            day_open=time(9, 0), day_close=time(14, 0)
        )

        # Create equity object
        self.equity_obj = Equity(
            instrument_id=self.instrument_id,
            broker_ticker=self.broker_ticker,
            data_ticker=self.data_ticker,
            midas_ticker=self.midas_ticker,
            security_type=self.security_type,
            currency=self.currency,
            exchange=self.exchange,
            fees=self.fees,
            initial_margin=self.initial_margin,
            quantity_multiplier=self.quantity_multiplier,
            price_multiplier=self.price_multiplier,
            company_name=self.company_name,
            industry=self.industry,
            market_cap=self.market_cap,
            shares_outstanding=self.shares_outstanding,
            slippage_factor=self.slippage_factor,
            trading_sessions=self.trading_sessions,
        )

    # Basic Validation
    def test_construction(self):
        # Test
        equity = Equity(
            instrument_id=self.instrument_id,
            broker_ticker=self.broker_ticker,
            data_ticker=self.data_ticker,
            midas_ticker=self.midas_ticker,
            security_type=self.security_type,
            currency=self.currency,
            exchange=self.exchange,
            fees=self.fees,
            initial_margin=self.initial_margin,
            quantity_multiplier=self.quantity_multiplier,
            price_multiplier=self.price_multiplier,
            company_name=self.company_name,
            industry=self.industry,
            market_cap=self.market_cap,
            shares_outstanding=self.shares_outstanding,
            slippage_factor=self.slippage_factor,
            trading_sessions=self.trading_sessions,
        )

        # Validate
        self.assertEqual(equity.data_ticker, self.data_ticker)
        self.assertIsInstance(equity.security_type, SecurityType)
        self.assertEqual(equity.data_ticker, self.data_ticker)
        self.assertEqual(equity.currency, self.currency)
        self.assertEqual(equity.exchange, self.exchange)
        self.assertEqual(equity.fees, self.fees)
        self.assertEqual(equity.initial_margin, self.initial_margin)
        self.assertEqual(equity.price_multiplier, self.price_multiplier)
        self.assertEqual(equity.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(equity.company_name, self.company_name)
        self.assertEqual(equity.industry, self.industry)
        self.assertEqual(equity.market_cap, self.market_cap)
        self.assertEqual(equity.shares_outstanding, self.shares_outstanding)
        self.assertEqual(equity.slippage_factor, self.slippage_factor)
        self.assertEqual(
            type(equity.contract),
            Contract,
            "contract shoudl be an instance of Contract",
        )

    def test_commission_fees(self):
        # Test
        fees = self.equity_obj.commission_fees(5)

        # Validate
        self.assertEqual(fees, 5 * self.fees * -1)

    def test_slippage_price_buy(self):
        current_price = 100

        # Test
        fees = self.equity_obj.slippage_price(
            current_price, action=Action.LONG
        )
        fees_2 = self.equity_obj.slippage_price(
            current_price, action=Action.COVER
        )

        # Validate
        self.assertEqual(fees, current_price + self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_slippage_price_sell(self):
        current_price = 100

        # Test
        fees = self.equity_obj.slippage_price(100, action=Action.SHORT)
        fees_2 = self.equity_obj.slippage_price(100, action=Action.SELL)

        # Validate
        self.assertEqual(fees, current_price - self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_value(self):
        quantity = 5
        price = 50

        # Test
        value = self.equity_obj.value(quantity, price)

        # Validate
        self.assertEqual(value, quantity * price)

    def test_cost(self):
        quantity = 5
        price = 50

        # Test
        cost = self.equity_obj.cost(quantity, price)

        # Validate
        self.assertEqual(cost, quantity * price)

    def test_to_dict(self):
        # Test
        equity_dict = self.equity_obj.to_dict()

        # Expected
        expected = {
            "ticker": self.midas_ticker,
            "security_type": self.security_type.value,
            "symbol_data": {
                "company_name": self.company_name,
                "venue": self.exchange.value,
                "currency": self.currency.value,
                "industry": self.industry.value,
                "market_cap": self.market_cap,
                "shares_outstanding": self.shares_outstanding,
            },
        }

        # Validate
        self.assertEqual(equity_dict, expected)

    def test_after_day_session(self):
        timestamp1 = 1727734758000000000  # 2024-09-30 18:19:18
        timestamp2 = 1727705958000000000  # 2024-09-30 10:19:18

        # Test
        self.assertTrue(self.equity_obj.after_day_session(timestamp1))
        self.assertFalse(self.equity_obj.after_day_session(timestamp2))

    def test_in_day_session(self):
        timestamp1 = 1727734758000000000  # 2024-09-30 18:19:18
        timestamp2 = 1727705958000000000  # 2024-09-30 10:19:18

        # Test
        self.assertFalse(self.equity_obj.in_day_session(timestamp1))
        self.assertTrue(self.equity_obj.in_day_session(timestamp2))

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(
            TypeError, "'instrument_id' must be of type int."
        ):
            Equity(
                instrument_id="str",
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'currency' must be enum instance Currency."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=12345,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'broker_ticker' must be of type str."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=1234,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'exchange' must be enum instance Venue."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=2345,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(TypeError, "'fees' must be int or float."):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees="1234",
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'initial_margin' must be an int or float."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin="12345",
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError,
            "'quantity_multiplier' must be type int or float.",
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier="12345",
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'price_multiplier' must be of type int or float."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier="12345",
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'company_name' must be of type str."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=1234,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'industry' must be of type Industry."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=1234,
                market_cap=self.market_cap,
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'market_cap' must be of type float."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap="12345",
                shares_outstanding=self.shares_outstanding,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'shares_outstanding' must be of type int."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding="12345",
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'slippage_factor' must be of type int or float."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=1234,
                slippage_factor="1",
            )

    # Value Constraints
    def test_value_constraint(self):
        with self.assertRaisesRegex(ValueError, "'fees' cannot be negative."):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=-1,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=1234,
                slippage_factor=1,
            )

        with self.assertRaisesRegex(
            ValueError, "'initial_margin' must be non-negative."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=-1,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=1234,
                slippage_factor=1,
            )

        with self.assertRaisesRegex(
            ValueError, "'price_multiplier' must be greater than zero."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=0,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=1234,
                slippage_factor=1,
            )

        with self.assertRaisesRegex(
            ValueError,
            "'quantity_multiplier' must be greater than 0.",
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=0,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=1234,
                slippage_factor=1,
            )

        with self.assertRaisesRegex(
            ValueError, "'slippage_factor' must be greater than zero."
        ):
            Equity(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                company_name=self.company_name,
                industry=self.industry,
                market_cap=self.market_cap,
                shares_outstanding=1234,
                slippage_factor=-1,
            )


class TestFuture(unittest.TestCase):
    def setUp(self) -> None:
        # Mock future data
        self.instrument_id = 1
        self.broker_ticker = "HEJ4"
        self.data_ticker = "HE"
        self.midas_ticker = "HE.n.0"
        self.security_type = SecurityType.FUTURE
        self.data_ticker = "HE.n.0"
        self.currency = Currency.USD
        self.exchange = Venue.CME
        self.fees = 0.1
        self.initial_margin = 4000.598
        self.quantity_multiplier = 40000
        self.price_multiplier = 0.01
        self.product_code = "HE"
        self.product_name = "Lean Hogs"
        self.industry = Industry.AGRICULTURE
        self.contract_size = 40000
        self.contract_units = ContractUnits.POUNDS
        self.tick_size = 0.00025
        self.min_price_fluctuation = 10
        self.continuous = False
        self.lastTradeDateOrContractMonth = "202406"
        self.slippage_factor = 10
        self.trading_sessions = TradingSession(
            day_open=time(9, 0), day_close=time(14, 0)
        )
        self.expr_months = [FuturesMonth.G, FuturesMonth.J, FuturesMonth.Z]
        self.term_day_rule = "nth_business_day_10"
        self.market_calendar = "CMEGlobex_Lean_Hog"

        # Create future object
        self.future_obj = Future(
            instrument_id=self.instrument_id,
            broker_ticker=self.broker_ticker,
            data_ticker=self.data_ticker,
            midas_ticker=self.midas_ticker,
            security_type=self.security_type,
            currency=self.currency,
            exchange=self.exchange,
            fees=self.fees,
            initial_margin=self.initial_margin,
            quantity_multiplier=self.quantity_multiplier,
            price_multiplier=self.price_multiplier,
            product_code=self.product_code,
            product_name=self.product_name,
            industry=self.industry,
            contract_size=self.contract_size,
            contract_units=self.contract_units,
            tick_size=self.tick_size,
            min_price_fluctuation=self.min_price_fluctuation,
            continuous=self.continuous,
            lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
            slippage_factor=self.slippage_factor,
            trading_sessions=self.trading_sessions,
            expr_months=self.expr_months,
            term_day_rule=self.term_day_rule,
            market_calendar=self.market_calendar,
        )

    # Basic Validation
    def test_contstruction(self):
        # Test
        future = Future(
            instrument_id=self.instrument_id,
            broker_ticker=self.broker_ticker,
            data_ticker=self.data_ticker,
            midas_ticker=self.midas_ticker,
            trading_sessions=self.trading_sessions,
            expr_months=self.expr_months,
            term_day_rule=self.term_day_rule,
            market_calendar=self.market_calendar,
            security_type=self.security_type,
            currency=self.currency,
            exchange=self.exchange,
            fees=self.fees,
            initial_margin=self.initial_margin,
            quantity_multiplier=self.quantity_multiplier,
            price_multiplier=self.price_multiplier,
            product_code=self.product_code,
            product_name=self.product_name,
            industry=self.industry,
            contract_size=self.contract_size,
            contract_units=self.contract_units,
            tick_size=self.tick_size,
            min_price_fluctuation=self.min_price_fluctuation,
            continuous=self.continuous,
            lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
            slippage_factor=self.slippage_factor,
        )
        # Validate
        self.assertEqual(future.midas_ticker, self.midas_ticker)
        self.assertIsInstance(future.security_type, SecurityType)
        self.assertEqual(future.data_ticker, self.data_ticker)
        self.assertEqual(future.currency, self.currency)
        self.assertEqual(future.exchange, self.exchange)
        self.assertEqual(future.fees, self.fees)
        self.assertEqual(future.initial_margin, self.initial_margin)
        self.assertEqual(future.price_multiplier, self.price_multiplier)
        self.assertEqual(future.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(future.product_code, self.product_code)
        self.assertEqual(future.product_name, self.product_name)
        self.assertEqual(future.industry, self.industry)
        self.assertEqual(future.contract_size, self.contract_size)
        self.assertEqual(future.contract_units, self.contract_units)
        self.assertEqual(future.tick_size, self.tick_size)
        self.assertEqual(
            future.min_price_fluctuation, self.min_price_fluctuation
        )
        self.assertEqual(future.continuous, self.continuous)
        self.assertEqual(
            future.lastTradeDateOrContractMonth,
            self.lastTradeDateOrContractMonth,
        )
        self.assertEqual(future.slippage_factor, self.slippage_factor)
        self.assertEqual(
            type(future.contract),
            Contract,
            "contract shoudl be an instance of Contract",
        )

    def test_commission_fees(self):
        quantity = 10

        # Test
        fees = self.future_obj.commission_fees(quantity)

        # Validate
        self.assertEqual(fees, quantity * self.fees * -1)

    def test_slippage_price_buy(self):
        current_price = 100

        # Test
        fees = self.future_obj.slippage_price(
            current_price, action=Action.LONG
        )
        fees_2 = self.future_obj.slippage_price(
            current_price, action=Action.COVER
        )

        # Validate
        self.assertEqual(fees, current_price + self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_slippage_price_sell(self):
        current_price = 100

        # Test
        fees = self.future_obj.slippage_price(100, action=Action.SHORT)
        fees_2 = self.future_obj.slippage_price(100, action=Action.SELL)

        # Validate
        self.assertEqual(fees, current_price - self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_value(self):
        quantity = 5
        price = 50

        # Test
        value = self.future_obj.value(quantity, price)

        # Expected
        expected_value = (
            self.quantity_multiplier * quantity * price * self.price_multiplier
        )

        # Validate
        self.assertEqual(value, expected_value)

    def test_cost(self):
        quantity = 5
        price = 50

        # Test
        cost = self.future_obj.cost(quantity, price)

        # Validate
        self.assertEqual(cost, quantity * self.initial_margin)

    def test_to_dict(self):
        # Test
        future_obj_dict = self.future_obj.to_dict()

        # Expected
        expected = {
            "ticker": self.midas_ticker,
            "security_type": self.security_type.value,
            "symbol_data": {
                "product_code": self.product_code,
                "product_name": self.product_name,
                "venue": self.exchange.value,
                "currency": self.currency.value,
                "industry": self.industry.value,
                "contract_size": self.contract_size,
                "contract_units": self.contract_units.value,
                "tick_size": self.tick_size,
                "min_price_fluctuation": self.min_price_fluctuation,
                "continuous": self.continuous,
            },
        }

        # Validate
        self.assertEqual(future_obj_dict, expected)

    def test_after_day_session(self):
        timestamp1 = 1727734758000000000  # 2024-09-30 18:19:18
        timestamp2 = 1727705958000000000  # 2024-09-30 10:19:18

        # Test
        self.assertTrue(self.future_obj.after_day_session(timestamp1))
        self.assertFalse(self.future_obj.after_day_session(timestamp2))

    def test_in_day_session(self):
        timestamp1 = 1727734758000000000  # 2024-09-30 18:19:18
        timestamp2 = 1727705958000000000  # 2024-09-30 10:19:18

        # Test
        self.assertFalse(self.future_obj.in_day_session(timestamp1))
        self.assertTrue(self.future_obj.in_day_session(timestamp2))

    def test_in_rolling_window(self):
        window = 2

        # Test
        timestamp = (
            1733930358000000000  # 2024-12-11 10:19:18 (2 business days before)
        )
        self.assertTrue(self.future_obj.in_rolling_window(timestamp, window))

        timestamp = (
            1733930358000000000  # 2024-12-15 10:19:18 (2 business days after)
        )
        self.assertTrue(self.future_obj.in_rolling_window(timestamp, window))

        timestamp = 1734362358000000000  # 2024-12-16 10:19:18
        self.assertFalse(self.future_obj.in_rolling_window(timestamp, window))

    def test_apply_day_rule_nth_day(self):
        month = 12
        year = 2024
        rule = "nth_business_day_10"

        # Test
        self.future_obj.term_day_rule = rule
        termination_date = self.future_obj.apply_day_rule(month, year)

        # Expected
        expected_date = pd.Timestamp("2024-12-13 00:00:00+0000")

        # Validate
        self.assertEqual(termination_date, expected_date)

    def test_apply_day_rule_nth_last_day(self):
        month = 10
        year = 2024
        rule = "nth_last_business_day_2"

        # Test
        self.future_obj.term_day_rule = rule
        termination_date = self.future_obj.apply_day_rule(month, year)

        # Expected
        expected_date = pd.Timestamp("2024-10-30 00:00:00+0000")

        # Validate
        self.assertEqual(termination_date, expected_date)

    def test_apply_day_rule_nth_business_day_before(self):
        month = 12
        year = 2024
        rule = "nth_bday_before_nth_day_1_15"

        # Test
        self.future_obj.term_day_rule = rule
        termination_date = self.future_obj.apply_day_rule(month, year)

        # Expected
        expected_date = pd.Timestamp("2024-12-13 00:00:00+0000")

        # Validate
        self.assertEqual(termination_date, expected_date)

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(
            TypeError, "'product_code' must be of type str."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=1234,
                product_name=self.product_name,
                industry=self.industry,
                contract_size=self.contract_size,
                contract_units=self.contract_units,
                tick_size=self.tick_size,
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=self.continuous,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'product_name' must be of type str."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=1234,
                industry=self.industry,
                contract_size=self.contract_size,
                contract_units=self.contract_units,
                tick_size=self.tick_size,
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=self.continuous,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'industry' must be of type Industry."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=self.product_name,
                industry=1234,
                contract_size=self.contract_size,
                contract_units=self.contract_units,
                tick_size=self.tick_size,
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=self.continuous,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'contract_size' must be of type int or float."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=self.product_name,
                industry=self.industry,
                contract_size="12345",
                contract_units=self.contract_units,
                tick_size=self.tick_size,
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=self.continuous,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'contract_units' must be of type ContractUnits."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=self.product_name,
                industry=self.industry,
                contract_size=self.contract_size,
                contract_units=1234,
                tick_size=self.tick_size,
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=self.continuous,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'tick_size' must be of type int or float."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=self.product_name,
                industry=self.industry,
                contract_size=self.contract_size,
                contract_units=self.contract_units,
                tick_size="1234",
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=self.continuous,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError,
            "'min_price_fluctuation' must be int or float.",
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=self.product_name,
                industry=self.industry,
                contract_size=self.contract_size,
                contract_units=self.contract_units,
                tick_size=self.tick_size,
                min_price_fluctuation="12345",
                continuous=self.continuous,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'continuous' must be of type boolean."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=self.product_name,
                industry=self.industry,
                contract_size=self.contract_size,
                contract_units=self.contract_units,
                tick_size=self.tick_size,
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=1234,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'lastTradeDateOrContractMonth' must be a string."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=self.product_name,
                industry=self.industry,
                contract_size=self.contract_size,
                contract_units=self.contract_units,
                tick_size=self.tick_size,
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=self.continuous,
                lastTradeDateOrContractMonth=12345,
                slippage_factor=self.slippage_factor,
            )

    # Value Constraint
    def test_value_constraints(self):
        with self.assertRaisesRegex(
            ValueError, "'tickSize' must be greater than zero."
        ):
            Future(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                expr_months=self.expr_months,
                term_day_rule=self.term_day_rule,
                market_calendar=self.market_calendar,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                product_code=self.product_code,
                product_name=self.product_name,
                industry=self.industry,
                contract_size=self.contract_size,
                contract_units=self.contract_units,
                tick_size=0,
                min_price_fluctuation=self.min_price_fluctuation,
                continuous=self.continuous,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=1,
            )


class TestOption(unittest.TestCase):
    def setUp(self) -> None:
        # Mock option data
        self.instrument_id = 1
        self.broker_ticker = "AAPLP"
        self.data_ticker = "AAPLP"
        self.midas_ticker = "AAPLP"
        self.security_type = SecurityType.OPTION
        self.data_ticker = "AAPL"
        self.currency = Currency.USD
        self.exchange = Venue.NASDAQ
        self.fees = 0.1
        self.initial_margin = 0
        self.quantity_multiplier = 100
        self.price_multiplier = 1
        self.strike_price = 109.99
        self.expiration_date = "2024-01-01"
        self.option_type = Right.CALL
        self.contract_size = 100
        self.underlying_name = "AAPL"
        self.lastTradeDateOrContractMonth = "20240201"
        self.slippage_factor = 1
        self.trading_sessions = TradingSession(
            day_open=time(9, 0), day_close=time(14, 0)
        )

        # Create option object
        self.option_obj = Option(
            instrument_id=self.instrument_id,
            broker_ticker=self.broker_ticker,
            data_ticker=self.data_ticker,
            midas_ticker=self.midas_ticker,
            trading_sessions=self.trading_sessions,
            security_type=self.security_type,
            currency=self.currency,
            exchange=self.exchange,
            fees=self.fees,
            initial_margin=self.initial_margin,
            quantity_multiplier=self.quantity_multiplier,
            price_multiplier=self.price_multiplier,
            strike_price=self.strike_price,
            expiration_date=self.expiration_date,
            option_type=self.option_type,
            contract_size=self.contract_size,
            underlying_name=self.underlying_name,
            lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
            slippage_factor=self.slippage_factor,
        )

    # Basic Validation
    def test_contstruction(self):
        # Test
        option = Option(
            instrument_id=self.instrument_id,
            broker_ticker=self.broker_ticker,
            data_ticker=self.data_ticker,
            midas_ticker=self.midas_ticker,
            trading_sessions=self.trading_sessions,
            security_type=self.security_type,
            currency=self.currency,
            exchange=self.exchange,
            fees=self.fees,
            initial_margin=self.initial_margin,
            quantity_multiplier=self.quantity_multiplier,
            price_multiplier=self.price_multiplier,
            strike_price=self.strike_price,
            expiration_date=self.expiration_date,
            option_type=self.option_type,
            contract_size=self.contract_size,
            underlying_name=self.underlying_name,
            lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
            slippage_factor=self.slippage_factor,
        )
        # Validate
        self.assertEqual(option.midas_ticker, self.midas_ticker)
        self.assertIsInstance(option.security_type, SecurityType)
        self.assertEqual(option.data_ticker, self.data_ticker)
        self.assertEqual(option.currency, self.currency)
        self.assertEqual(option.exchange, self.exchange)
        self.assertEqual(option.fees, self.fees)
        self.assertEqual(option.initial_margin, self.initial_margin)
        self.assertEqual(option.price_multiplier, self.price_multiplier)
        self.assertEqual(option.quantity_multiplier, self.quantity_multiplier)
        self.assertEqual(option.strike_price, self.strike_price)
        self.assertEqual(option.expiration_date, self.expiration_date)
        self.assertEqual(option.option_type, self.option_type)
        self.assertEqual(option.contract_size, self.contract_size)
        self.assertEqual(option.underlying_name, self.underlying_name)
        self.assertEqual(
            option.lastTradeDateOrContractMonth,
            self.lastTradeDateOrContractMonth,
        )
        self.assertEqual(option.slippage_factor, self.slippage_factor)
        self.assertEqual(
            type(option.contract),
            Contract,
            "contract shoudl be an instance of Contract",
        )

    def test_commission_fees(self):
        quantity = 10

        # Test
        fees = self.option_obj.commission_fees(quantity)

        # Validate
        self.assertEqual(fees, quantity * self.fees * -1)

    def test_slippage_price_buy(self):
        current_price = 100

        # Test
        fees = self.option_obj.slippage_price(
            current_price, action=Action.LONG
        )
        fees_2 = self.option_obj.slippage_price(
            current_price, action=Action.COVER
        )

        # Validate
        self.assertEqual(fees, current_price + self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_slippage_price_sell(self):
        current_price = 100

        # Test
        fees = self.option_obj.slippage_price(100, action=Action.SHORT)
        fees_2 = self.option_obj.slippage_price(100, action=Action.SELL)

        # Validate
        self.assertEqual(fees, current_price - self.slippage_factor)
        self.assertEqual(fees, fees_2)

    def test_cost(self):
        quantity = 5
        price = 50

        # Test
        cost = self.option_obj.cost(quantity, price)

        # Validate
        self.assertEqual(cost, quantity * price * self.quantity_multiplier)

    def test_value(self):
        quantity = 5
        price = 50

        # Test
        value = self.option_obj.value(quantity, price)

        # Validate
        self.assertEqual(value, quantity * price * self.quantity_multiplier)

    def test_to_dict(self):
        # Test
        option_dict = self.option_obj.to_dict()

        # Expected
        expected = {
            "ticker": self.midas_ticker,
            "security_type": self.security_type.value,
            "symbol_data": {
                "strike_price": self.strike_price,
                "currency": self.currency.value,
                "venue": self.exchange.value,
                "expiration_date": self.expiration_date,
                "option_type": self.option_type.value,
                "contract_size": self.contract_size,
                "underlying_name": self.underlying_name,
            },
        }

        # Validate
        self.assertEqual(option_dict, expected)

    # Type Constraint
    def test_type_constraints(self):
        with self.assertRaisesRegex(
            TypeError, "'strike_price' must be of type int or float."
        ):
            Option(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                strike_price="12345",
                expiration_date=self.expiration_date,
                option_type=self.option_type,
                contract_size=self.contract_size,
                underlying_name=self.underlying_name,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'expiration_date' must be of type str."
        ):
            Option(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                strike_price=self.strike_price,
                expiration_date=12345,
                option_type=self.option_type,
                contract_size=self.contract_size,
                underlying_name=self.underlying_name,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'option_type' must be of type Right."
        ):
            Option(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                strike_price=self.strike_price,
                expiration_date=self.expiration_date,
                option_type=12345,
                contract_size=self.contract_size,
                underlying_name=self.underlying_name,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'contract_size' must be of type int or float."
        ):
            Option(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                strike_price=self.strike_price,
                expiration_date=self.expiration_date,
                option_type=self.option_type,
                contract_size="1234",
                underlying_name=self.underlying_name,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'underlying_name' must be of type str."
        ):
            Option(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                strike_price=self.strike_price,
                expiration_date=self.expiration_date,
                option_type=self.option_type,
                contract_size=self.contract_size,
                underlying_name=1234,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=self.slippage_factor,
            )

        with self.assertRaisesRegex(
            TypeError, "'lastTradeDateOrContractMonth' must be a string."
        ):
            Option(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                strike_price=self.strike_price,
                expiration_date=self.expiration_date,
                option_type=self.option_type,
                contract_size=self.contract_size,
                underlying_name=self.underlying_name,
                lastTradeDateOrContractMonth=1234,
                slippage_factor=self.slippage_factor,
            )

    # Value Constraint
    def test_value_constraint(self):
        with self.assertRaisesRegex(
            ValueError, "'strike' must be greater than zero."
        ):
            Option(
                instrument_id=self.instrument_id,
                broker_ticker=self.broker_ticker,
                data_ticker=self.data_ticker,
                midas_ticker=self.midas_ticker,
                trading_sessions=self.trading_sessions,
                security_type=self.security_type,
                currency=self.currency,
                exchange=self.exchange,
                fees=self.fees,
                initial_margin=self.initial_margin,
                quantity_multiplier=self.quantity_multiplier,
                price_multiplier=self.price_multiplier,
                strike_price=0,
                expiration_date=self.expiration_date,
                option_type=self.option_type,
                contract_size=self.contract_size,
                underlying_name=self.underlying_name,
                lastTradeDateOrContractMonth=self.lastTradeDateOrContractMonth,
                slippage_factor=1,
            )


class TestSymbolFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.future_dict = {
            "type": "Future",
            "instrument_id": 43,
            "broker_ticker": "HE",
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
            "lastTradeDateOrContractMonth": "202412",
            "slippage_factor": 0,
            "trading_sessions": {"day_open": "09:30", "day_close": "14:05"},
            "expr_months": ["G", "J", "K", "M", "N", "Q", "V", "Z"],
            "term_day_rule": "nth_business_day_10",
            "market_calendar": "CMEGlobex_Lean_Hog",
        }

    def test_from_dict(self):
        # Test
        symbol = SymbolFactory.from_dict(self.future_dict)

        # Validate
        self.assertIsInstance(symbol, Future)


class TestSymbolMap(unittest.TestCase):
    def setUp(self) -> None:
        self.future_dict = {
            "type": "Future",
            "instrument_id": 43,
            "broker_ticker": "HE",
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
            "lastTradeDateOrContractMonth": "202412",
            "slippage_factor": 0,
            "trading_sessions": {"day_open": "09:30", "day_close": "14:05"},
            "expr_months": ["G", "J", "K", "M", "N", "Q", "V", "Z"],
            "term_day_rule": "nth_business_day_10",
            "market_calendar": "CMEGlobex_Lean_Hog",
        }
        self.symbol = SymbolFactory.from_dict(self.future_dict)
        self.symbols_map = SymbolMap()

    def test_add_symbol(self):
        # Test
        self.symbols_map.add_symbol(self.symbol)

        # Validate
        id = self.symbol.instrument_id

        self.assertEqual(self.symbols_map.map[id], self.symbol)
        self.assertEqual(
            self.symbols_map.broker_map[self.symbol.broker_ticker], id
        )
        self.assertEqual(
            self.symbols_map.data_map[self.symbol.data_ticker], id
        )
        self.assertEqual(
            self.symbols_map.midas_map[self.symbol.midas_ticker], id
        )

    def test_get_symbol(self):
        self.symbols_map.add_symbol(self.symbol)

        # Test
        a = self.symbols_map.get_symbol(self.symbol.broker_ticker)
        b = self.symbols_map.get_symbol(self.symbol.data_ticker)
        c = self.symbols_map.get_symbol(self.symbol.midas_ticker)

        # Validate
        self.assertEqual(a, self.symbol)
        self.assertEqual(b, self.symbol)
        self.assertEqual(c, self.symbol)

    def test_get_id(self):
        self.symbols_map.add_symbol(self.symbol)

        # Test
        a = self.symbols_map.get_id(self.symbol.broker_ticker)
        b = self.symbols_map.get_id(self.symbol.data_ticker)
        c = self.symbols_map.get_id(self.symbol.midas_ticker)

        # Validate
        id = self.symbol.instrument_id

        self.assertEqual(a, id)
        self.assertEqual(b, id)
        self.assertEqual(c, id)

    def test_properties(self):
        self.symbols_map.add_symbol(self.symbol)

        # Test
        symbols = self.symbols_map.symbols
        ids = self.symbols_map.instrument_ids
        broker = self.symbols_map.broker_tickers
        data = self.symbols_map.data_tickers
        midas = self.symbols_map.midas_tickers

        # Validate
        self.assertEqual(symbols, [self.symbol])
        self.assertEqual(ids, [43])
        self.assertEqual(broker, ["HE"])
        self.assertEqual(data, ["HE"])
        self.assertEqual(midas, ["HE.n.0"])


# class TestIndex(unittest.TestCase):
#     def setUp(self) -> None:
#         # Mock index data
#         self.ticker = "GSPC"
#         self.security_type = SecurityType.INDEX
#         self.name = "S&P 500"
#         self.currency = Currency.USD
#         self.asset_class = AssetClass.EQUITY
#
#         # Create index object
#         self.index_obj = Index(
#             ticker=self.ticker,
#             security_type=self.security_type,
#             name=self.name,
#             currency=self.currency,
#             asset_class=self.asset_class,
#         )
#
#     # Basic Validation
#     def test_contstruction(self):
#         # Test
#         index = Index(
#             ticker=self.ticker,
#             security_type=self.security_type,
#             name=self.name,
#             currency=self.currency,
#             asset_class=self.asset_class,
#         )
#         # Validate
#         self.assertEqual(index.ticker, self.ticker)
#         self.assertEqual(index.security_type, self.security_type)
#         self.assertEqual(index.name, self.name)
#         self.assertEqual(index.exchange, Venue.INDEX)
#         self.assertEqual(index.currency, self.currency)
#         self.assertEqual(index.asset_class, self.asset_class)
#
#     def test_to_dict(self):
#         # Test
#         index_dict = self.index_obj.to_dict()
#
#         # Expected
#         expected = {
#             "ticker": self.ticker,
#             "security_type": self.security_type.value,
#             "symbol_data": {
#                 "name": self.name,
#                 "currency": self.currency.value,
#                 "asset_class": self.asset_class.value,
#                 "venue": Venue.INDEX.value,
#             },
#         }
#
#         # Validate
#         self.assertEqual(index_dict, expected)
#
#     # Type Constraint
#     def test_type_constraints(self):
#         with self.assertRaisesRegex(
#             TypeError, "'name' must be of type str."
#         ):
#             Index(
#                 ticker=self.ticker,
#                 security_type=self.security_type,
#                 name=12345,
#                 currency=self.currency,
#                 asset_class=self.asset_class,
#             )
#
#         with self.assertRaisesRegex(
#             TypeError, "'asset_class' must be of type AssetClass."
#         ):
#             Index(
#                 ticker=self.ticker,
#                 security_type=self.security_type,
#                 name=self.name,
#                 currency=self.currency,
#                 asset_class=12345,
#             )


if __name__ == "__main__":
    unittest.main()

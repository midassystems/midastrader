import unittest
import numpy as np

from midas.shared.account import Account, AccountDetails, EquityDetails

class AccountTest(unittest.TestCase):
    def setUp(self) -> None:
        # Create account object
        self.timestamp=np.uint64(1704214800000000000)
        self.FullAvailableFunds=502398.7799999999
        self.FullInitMarginReq=497474.57
        self.NetLiquidation=999873.3499999999
        self.UnrealizedPnL=1234
        self.FullMaintMarginReq=12345
        self.ExcessLiquidity=9876543
        self.Currency="USD"
        self.BuyingPower=765432
        self.FuturesPNL=76543
        self.TotalCashBalance=4321

        self.account_obj = Account(self.timestamp,
                            self.FullAvailableFunds,
                            self.FullInitMarginReq,
                            self.NetLiquidation,
                            self.UnrealizedPnL,
                            self.FullMaintMarginReq,
                            self.ExcessLiquidity, 
                            self.Currency,
                            self.BuyingPower,
                            self.FuturesPNL,
                            self.TotalCashBalance
                        )

    
    # Basic Validation
    def test_construction(self):
        # Test
        account = Account(self.timestamp,
                            self.FullAvailableFunds,
                            self.FullInitMarginReq,
                            self.NetLiquidation,
                            self.UnrealizedPnL,
                            self.FullMaintMarginReq,
                            self.ExcessLiquidity, 
                            self.Currency,
                            self.BuyingPower,
                            self.FuturesPNL,
                            self.TotalCashBalance
                        )
        
        # validate
        self.assertIsInstance(account, Account)

    def test_capital(self):
        # Test
        capital = self.account_obj.capital

        # Validate
        self.assertEqual(capital, self.FullAvailableFunds)

    def test_equity_value(self):
        # Test
        equity_value = self.account_obj.equity_value()

        # Expected
        expected = EquityDetails(timestamp=self.timestamp, equity_value=round(self.NetLiquidation, 2))

        # Validate
        self.assertEqual(equity_value, expected)

    def test_check_margin_call_true(self):
        self.account_obj.full_available_funds = 0

        # Test
        result = self.account_obj.check_margin_call()

        # Validate
        self.assertTrue(result)

    def test_check_margin_call_false(self):
        # Test
        result = self.account_obj.check_margin_call()

        # Validate
        self.assertFalse(result)

    def test_to_dict(self):
        # Test
        account_dict = self.account_obj.to_dict()

        # Expected
        expected = AccountDetails(
            timestamp=self.timestamp,
            full_available_funds=self.FullAvailableFunds,
            full_init_margin_req=self.FullInitMarginReq,
            net_liquidation=self.NetLiquidation,
            unrealized_pnl=self.UnrealizedPnL,
            full_maint_margin_req=self.FullMaintMarginReq,
            excess_liquidity=self.ExcessLiquidity,
            currency=self.Currency,
            buying_power=self.BuyingPower,
            futures_pnl=self.FuturesPNL,
            total_cash_balance=self.TotalCashBalance
        )

        # Validate
        self.assertEqual(account_dict, expected)

    def test_pretty_print(self):
        # Test
        account_str = self.account_obj.pretty_print()

        # Validate
        self.assertEqual(type(account_str), str)

if __name__ =="__main__":
    unittest.main()
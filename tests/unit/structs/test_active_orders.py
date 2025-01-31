import unittest
from midastrader.structs.active_orders import ActiveOrder


class ActiceOrderTest(unittest.TestCase):
    def test_creation(self):
        # Test
        order = ActiveOrder(
            permId=1,
            clientId=22,
            orderId=5,
            parentId=5,
            account="DU12546",
            instrument=1234,
            secType="STK",
            exchange="NASDAQ",
            action="BUY",
            orderType="MKT",
            totalQty=1009.90,
            cashQty=109.99,
            lmtPrice=0.0,
            auxPrice=0.0,
            status="Submitted",
            filled=9.0,
            remaining=10,
            avgFillPrice=100,
            lastFillPrice=100,
            whyHeld="",
            mktCapPrice=1000.99,
        )

        # Validate
        self.assertEqual(type(order), ActiveOrder)


if __name__ == "__main__":
    unittest.main()

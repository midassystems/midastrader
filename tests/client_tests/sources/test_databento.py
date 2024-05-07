import unittest
from decouple import config

from midas.client.sources.databento import *

DATABENTO_KEY=config('DATABENTO_API_KEY')

class TestDatabentoClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = DatabentoClient(DATABENTO_KEY)
    
    def setUp(self) -> None:
        self.symbols = ['ZC.n.0'] # 'n' Will rank the expirations by the open interest at the previous day's close
        self.schema = Schemas.Trades
        self.dataset = Datasets.CME
        self.stype = Symbology.CONTINUOSCONTRACT
        self.start_date="2024-02-06T12:00:00"
        self.end_date="2024-02-06T12:10:00"

    def test_get_cost(self):
        # test
        response=self.client.get_size(self.dataset, self.symbols, self.schema, self.stype,self.start_date, self.end_date )
        
        # validate
        self.assertEqual(type(response), float)
        self.assertTrue(response > 0)

    def test_get_size(self):
        # test
        response=self.client.get_cost(self.dataset, self.symbols, self.schema, self.stype,self.start_date, self.end_date)
        
        # validate
        self.assertEqual(type(response), float)
        self.assertTrue(response > 0)

    def test_get_historical_bars(self):
        schema=Schemas.OHLCV_1m

        # test
        response=self.client.get_historical_bar(self.dataset, self.symbols, schema, self.stype, self.start_date, self.end_date)
        df=response.to_df()
        
        # validate
        self.assertEqual(response.schema, schema.value)
        self.assertTrue(len(df) > 0)

if __name__ == "__main__":
    unittest.main()
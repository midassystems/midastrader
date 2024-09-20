import unittest
import numpy as np
import pandas as pd
from queue import Queue
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock
from midas.engine.events import MarketEvent
from midas.engine.order_book.test_order_book import OrderBook
from midas.shared.market_data import BarData
from midas.engine.gateways.backtest.test_data_client import DataClient


def process_db_response(db_response: list):
    """Create Properly processed response."""
    df = pd.DataFrame(db_response)
    df.drop(columns=["id"], inplace=True)
    df["timestamp"] = df["timestamp"].astype(np.uint64)
    df["open"] = df["open"].apply(Decimal)
    df["high"] = df["high"].apply(Decimal)
    df["low"] = df["low"].apply(Decimal)
    df["close"] = df["close"].apply(Decimal)
    df["volume"] = df["volume"].astype(np.uint64)
    processed_df = df.sort_values(by="timestamp", ascending=True).reset_index(drop=True)
    return processed_df


class TestDataClient(unittest.TestCase):
    def setUp(self) -> None:
        # Mock objects
        self.event_queue = Mock()
        self.mock_db_client = Mock()
        self.mock_order_book = OrderBook(self.event_queue)
        self.eod_event_flag = Mock()

        # Dataclient instance
        self.data_client = DataClient(
            event_queue=self.event_queue,
            data_client=self.mock_db_client,
            order_book=self.mock_order_book,
            eod_event_flag=self.eod_event_flag,
        )

    def test_get_data(self):
        tickers = ["HE.n.0", "ZC.n.0"]
        start = "2024-01-01"
        end = "2024-12-01"
        schema = "ohlcv-1m"

        respone = self.data_client.get_data(tickers, start, end, schema)

        # print(self.data_client.data)

    def test_data_stream(self):
        tickers = ["HE.n.0", "ZC.n.0"]
        start = "2023-01-01"
        end = "2024-12-01"
        schema = "ohlcv-1m"
        self.data_client.get_data(tickers, start, end, schema)

        # Test
        while self.data_client.data_stream():
            continue


if __name__ == "__main__":
    unittest.main()

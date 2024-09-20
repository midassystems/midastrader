import threading
import numpy as np
import pandas as pd
from typing import List, Optional
from queue import Queue
from decimal import Decimal
from dateutil import parser
from datetime import datetime
from mbn import Schema, BufferStore, RecordMsg
from midasClient.client import DatabaseClient, RetrieveParams
from midas.utils.unix import unix_to_iso
from midas.engine.events import MarketEvent, EODEvent
from midas.engine.components.gateways.base_data_client import BaseDataClient
from midas.engine.components.order_book import OrderBook

# from midas.client import DatabaseClient
# from quantAnalytics.dataprocessor import DataProcessor
# from midas.shared.market_data import BarData, QuoteData


class DataClient(BaseDataClient, DatabaseClient):
    """
    Manages data fetching, processing, and streaming for trading simulations, extending the DatabaseClient for specific trading data operations.

    This class is responsible for interacting with the database to fetch historical market data,
    processing it according to specified parameters, and streaming it to simulate live trading conditions in a backtest environment.

    Attributes:
    - event_queue (Queue): The queue used for posting market data and end-of-day events.
    - data_client (DatabaseClient): A client class based on a Django Rest-Framework API for interacting with the database.
    - order_book (OrderBook): The order book where market data is posted for trading operations.
    """

    def __init__(
        self,
        event_queue: Queue,
        data_client: DatabaseClient,
        order_book: OrderBook,
        eod_event_flag: threading.Event,
    ):
        """
        Initializes the DataClient with the necessary components for market data management.

        Parameters:
        - event_queue (Queue): The main event queue for posting data-related events.
        - data_client (DatabaseClient): The database client used for retrieving market data.
        - order_book (OrderBook): The order book where the market data will be used for trading operations.
        """
        self.event_queue = event_queue
        self.data_client = data_client
        self.order_book = order_book
        self.eod_event_flag = eod_event_flag
        if self.eod_event_flag:
            self.eod_event_flag.set()

        # Data
        self.data: BufferStore  # pd.DataFrame
        self.unique_timestamps: list
        self.next_date = None
        self.current_date_index = 0
        self.current_day = None

    def get_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        schema: Schema,
        data_file_path: Optional[str] = None,  # New argument for file path
    ) -> bool:
        """
        Retrieves historical market data from the database or a file and initializes the data processing.

        Parameters:
        - tickers (List[str]): A list of ticker symbols (e.g., ['AAPL', 'MSFT']).
        - start_date (str): The start date for the data retrieval in ISO format 'YYYY-MM-DD'.
        - end_date (str): The end date for the data retrieval in ISO format 'YYYY-MM-DD'.
        - missing_values_strategy (str): Strategy to handle missing values, either 'drop' or 'fill_forward'.
        - data_file_path (Optional[str]): Path to the file containing the historical data. If provided, data will be loaded from the file instead of the database.

        Returns:
        - bool: True if data retrieval and initial processing are successful.
        """
        print(data_file_path)
        if data_file_path:
            self.data = BufferStore.from_file(data_file_path)
        else:
            params = RetrieveParams(tickers, start_date, end_date, schema)
            self.data = self.data_client.get_records(params)

        return True

    # --  SIMULATE DATA STREAM --
    def data_stream(self) -> bool:
        record = self.data.replay()

        if record is None:
            return False

        # Update the next_date here
        self.next_date = record.hd.ts_event
        iso = unix_to_iso(self.next_date)
        next_day = parser.parse(iso).date()

        if self.current_day is None or next_day != self.current_day:
            if self.current_day is not None:
                # Perform EOD operations for the previous day
                self.eod_event_flag.clear()
                self._process_eod(self.current_day)

            # Update the current day
            self.current_day = next_day

        # Non-blocking wait with timeout
        while not self.eod_event_flag.is_set():
            self.eod_event_flag.wait(timeout=0.1)
            if not self.event_queue.empty():
                return True

        # Update market data
        self._set_market_data(record)

        return True

    def _process_eod(self, current_day):
        """
        Processes End-of-Day operations.

        Parameters:
        - current_day (datetime.date): The current day to process EOD operations.
        """
        self.event_queue.put(EODEvent(timestamp=current_day))

    def _set_market_data(self, record: RecordMsg):
        """
        Posts the latest market data to the order book for trading simulation.
        """
        id = record.hd.instrument_id
        ticker = self.data.metadata.mappings.get_ticker(id)
        self.order_book.update(record, ticker)

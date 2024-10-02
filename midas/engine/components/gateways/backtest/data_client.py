from typing import List, Optional
from mbn import Schema, BufferStore, RecordMsg
from midasClient.client import DatabaseClient, RetrieveParams
from midas.utils.unix import unix_to_iso
from midas.engine.events import EODEvent
from midas.engine.components.gateways.base import BaseDataClient
from midas.engine.components.observer.base import Subject, EventType
from midas.symbol import SymbolMap
from datetime import datetime
from midas.utils.logger import SystemLogger


class DataClient(Subject, BaseDataClient):
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
        database_client: DatabaseClient,
        symbols_map: SymbolMap,
    ):
        """
        Initializes the DataClient with the necessary components for market data management.

        Parameters:
        - event_queue (Queue): The main event queue for posting data-related events.
        - data_client (DatabaseClient): The database client used for retrieving market data.
        - order_book (OrderBook): The order book where the market data will be used for trading operations.
        """
        super().__init__()
        self.logger = SystemLogger.get_logger()
        self.database_client = database_client
        self.symbols_map = symbols_map
        self.data: BufferStore
        self.last_ts = None
        self.next_date = None
        self.current_date = None
        self.eod_triggered = False

    def load_backtest_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        schema: Schema,
        data_file_path: Optional[str] = None,
    ) -> bool:
        """Loads backtest data."""

        self.data = self.get_data(
            tickers,
            start_date,
            end_date,
            schema,
            data_file_path,
        )

        return True

    def get_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        schema: Schema,
        data_file_path: Optional[str] = None,
    ) -> BufferStore:
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
        if data_file_path:
            data = BufferStore.from_file(data_file_path)
        else:
            params = RetrieveParams(tickers, start_date, end_date, schema)
            data = self.database_client.get_records(params)

        return data

    def data_stream(self) -> bool:
        """
        Simulate data stream.
        """
        record = self.data.replay()

        if record is None:
            return False

        # Adjust instrument id
        id = record.hd.instrument_id
        ticker = self.data.metadata.mappings.get_ticker(id)
        new_id = self.symbols_map.get_symbol(ticker).instrument_id
        record.instrument_id = new_id

        # Check for end of trading da
        self._check_eod(record)

        # Update market data
        self.notify(EventType.MARKET_DATA, record)
        # elf.notify_market_data(record)

        return True

    def _check_eod(self, record: RecordMsg):
        """
        Checks if the current record marks the end of a trading day.
        """
        ts = datetime.fromisoformat(
            unix_to_iso(record.ts_event, tz_info="America/New_York")
        )
        date = ts.date()

        if not self.current_date or date > self.current_date:
            self.current_date = date
            self.eod_triggered = False

        symbol = self.symbols_map.map[record.instrument_id]

        if not self.eod_triggered and symbol.after_day_session(
            record.ts_event
        ):
            self.logger.info("EOD triggered")
            self.eod_triggered = True
            self.notify(
                EventType.EOD_EVENT,
                EODEvent(timestamp=self.current_date),
            )

            # self.notify_eod_event()

    # def notify_eod_event(self):
    #     """
    #     Processes End-of-Day operations.
    #
    #     Parameters:
    #     - current_day (datetime.date): The current day to process EOD operations.
    #     """
    #     self.notify(EventType.EOD_EVENT, EODEvent(timestamp=self.current_date))
    #
    # def notify_market_data(self, record: RecordMsg):
    #     """
    #     Posts the latest market data to the order book for trading simulation.
    #     """
    #     self.notify(EventType.MARKET_DATA, record)

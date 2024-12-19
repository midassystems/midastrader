from typing import Optional
from mbn import BufferStore, RecordMsg
from midasClient.client import DatabaseClient
from midasClient.historical import RetrieveParams
from midas.utils.unix import unix_to_iso
from midas.engine.events import EODEvent
from midas.engine.components.gateways.base import BaseDataClient
from midas.engine.components.observer.base import Subject, EventType
from midas.symbol import SymbolMap
from datetime import datetime
from midas.utils.logger import SystemLogger
from midas.engine.config import Parameters


class DataClient(Subject, BaseDataClient):
    """
    Manages data fetching, processing, and streaming for trading simulations, extending the DatabaseClient for specific trading data operations.

    This class is responsible for interacting with the database to fetch historical market data,
    processing it according to specified parameters, and streaming it to simulate live trading conditions in a backtest environment.

    Attributes:
        database_client (DatabaseClient): A client class based on a Django Rest-Framework API for interacting with the database.
        symbols_map (SymbolMap): Maps symbols to unique identifiers for instruments.
        data (BufferStore): A buffer storing historical market data.
        last_ts (Optional[int]): The timestamp of the last processed record.
        next_date (Optional[datetime.date]): The next date for processing data.
        current_date (Optional[datetime.date]): The current trading date being processed.
        eod_triggered (bool): Flag indicating if the end-of-day event has been triggered for the current date.
    """

    def __init__(
        self,
        database_client: DatabaseClient,
        symbols_map: SymbolMap,
    ):
        """
        Initializes the DataClient with the necessary components for market data management.

        Args:
            database_client (DatabaseClient): The database client used for retrieving market data.
            symbols_map (SymbolMap): Mapping of symbols to unique identifiers for instruments.
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

    def get_data(
        self,
        parameters: Parameters,
        data_file_path: Optional[str] = None,
    ) -> bool:
        """
        Retrieve historical market data from the database or a file and initialize the data processing.

        Args:
            parameters (Parameters):
                A `Parameters` object containing the following:
                - `tickers` (List[str]): List of ticker symbols (e.g., ['AAPL', 'MSFT']).
                - `start` (str): The start date for data retrieval in ISO format ('YYYY-MM-DD').
                - `end` (str): The end date for data retrieval in ISO format ('YYYY-MM-DD').
                - `schema` (Schema): Schema defining the structure of the data.
            data_file_path (Optional[str]):
                Path to the file containing the historical data. If provided, data will be loaded from the file instead of the database.

        Returns:
            bool: True if data retrieval is successful.
        """
        if data_file_path:
            data = BufferStore.from_file(data_file_path)
            metadata = data.metadata
            parameters.start = unix_to_iso(metadata.start)
            parameters.end = unix_to_iso(metadata.end)
            parameters.schema = metadata.schema.__str__()
        else:
            params = RetrieveParams(
                parameters.tickers,
                parameters.start,
                parameters.end,
                parameters.schema,
            )
            data = self.database_client.historical.get_records(params)

        self.data = data
        return True

    def next_record(self) -> RecordMsg:
        """
        Retrieves the next record from the data buffer and adjusts its instrument ID.

        Returns:
            RecordMsg: The next record with updated instrument ID.
        """
        record = self.data.replay()

        if record is None:
            return None

        # Adjust instrument id
        id = record.hd.instrument_id
        ticker = self.data.metadata.mappings.get_ticker(id)
        new_id = self.symbols_map.get_symbol(ticker).instrument_id
        record.instrument_id = new_id

        return record

    def data_stream(self) -> bool:
        """
        Simulates streaming of market data by processing the next record in the data buffer.

        Returns:
            bool: True if a record was processed, False if no more records are available.
        """

        record = self.next_record()

        if record is None:
            return False

        # Check for end of trading da
        self._check_eod(record)

        # Update market data
        self.notify(EventType.MARKET_DATA, record)

        return True

    def _check_eod(self, record: RecordMsg) -> None:
        """
        Checks if the current record marks the end of a trading day and triggers the end-of-day event if necessary.

        Args:
            record (RecordMsg): The current record being processed.
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
            self.logger.debug("EOD triggered")
            self.eod_triggered = True
            self.notify(
                EventType.EOD_EVENT,
                EODEvent(timestamp=self.current_date),
            )

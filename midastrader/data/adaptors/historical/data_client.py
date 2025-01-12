import threading
from mbn import BufferStore, RecordMsg
from midas_client.client import DatabaseClient
from midas_client.historical import RetrieveParams
from datetime import datetime

from midastrader.utils.unix import unix_to_iso
from midastrader.structs.events import EODEvent
from midastrader.structs.symbol import SymbolMap
from midastrader.config import Parameters, Mode
from midastrader.data.adaptors.base import DataAdapter
from midastrader.message_bus import MessageBus, EventType


class HistoricalAdaptor(DataAdapter):
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

    def __init__(self, symbols_map: SymbolMap, bus: MessageBus, **kwargs):
        """
        Initializes the DataClient with the necessary components for market data management.

        Args:
            database_client (DatabaseClient): The database client used for retrieving market data.
            symbols_map (SymbolMap): Mapping of symbols to unique identifiers for instruments.
        """
        super().__init__(symbols_map, bus)
        self.data_file = kwargs["data_file"]
        self.database_client = DatabaseClient()
        self.data: BufferStore = None
        self.mode: Mode = None
        self.last_ts = None
        self.next_date = None
        self.current_date = None
        self.eod_triggered = False
        self.eod_event = threading.Event()  # Thread-safe synchronization

        # Subscriptions
        self.data_processed_flag = self.bus.subscribe(EventType.DATA_PROCESSED)

    def process(self):
        """
        Main processing loop that streams data and handles EOD synchronization.
        """
        self.logger.info("HistoricalAdaptor running ...")
        self.running.set()

        while self.data_stream():
            if self.shutdown_event.is_set():
                break
            continue

        self.cleanup()

    def cleanup(self):
        """
        Main processing loop that streams data and handles EOD synchronization.
        """
        self.logger.info("Data Engine - stream done")

    def set_mode(self, mode: Mode) -> None:
        self.mode = mode

    def get_data(self, parameters: Parameters) -> bool:
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
        if self.data_file:
            data = BufferStore.from_file(self.data_file)
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
            self.logger.info("No more records in historical stream.")
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
        if self.mode == Mode.BACKTEST:
            self._check_eod(record)

        # Update market data
        self.bus.publish(EventType.DATA, record)

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
            self.bus.publish(EventType.EOD_PROCESSED, False)  # Reset flag

        symbol = self.symbols_map.map[record.instrument_id]

        if not self.eod_triggered and symbol.after_day_session(
            record.ts_event
        ):
            self.logger.debug("Data Engine - EOD triggered")
            self.eod_triggered = True
            self.bus.publish(
                EventType.DATA,
                EODEvent(timestamp=self.current_date),
            )
            self._await_data_processed()

    def _await_data_processed(self):
        """
        Waits for the EOD_PROCESSED flag to be set.
        """
        self.logger.debug("Data Engine - Waiting for data processed flag...")
        while True:
            if self.bus.get_flag(EventType.DATA_PROCESSED):
                self.logger.debug("Data Engine - EOD processed ...")
                self.bus.publish(EventType.DATA_PROCESSED, False)
                break

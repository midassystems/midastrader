# client.py
import threading
from enum import Enum
from ibapi.contract import Contract
from mbn import BboMsg, BidAskPair, Side

from midastrader.data.adaptors.ib.wrapper import DataApp
from midastrader.data.adaptors.base import DataAdapter
from midastrader.structs.symbol import SymbolMap
from midastrader.message_bus import MessageBus
from midastrader.utils.logger import SystemLogger


class LiveDataType(Enum):
    TICK = "TICK"
    BAR = "BAR"


class IBAdaptor(DataAdapter):
    """
    Manages the data connection to the Interactive Brokers (IB) server. Handles various data requests,
    such as quotes and bars, through a WebSocket connection. Ensures thread-safe operations with locks.

    Attributes:
        event_queue (Queue): Queue for managing asynchronous events received from the IB server.
        order_book (OrderBook): Instance of OrderBook for maintaining and updating live order book data.
        logger (logging.Logger): Logger for recording operational logs, errors, or informational messages.
        host (str): Hostname or IP address of the IB data server.
        port (int): Port number of the IB data server.
        clientId (str): Unique identifier for the client connecting to the IB data server.
        account (str): IB account identifier associated with this connection.
        lock (Lock): Threading lock to ensure thread-safe operations.

    Methods:
        connect(): Establishes a WebSocket connection to the IB server.
        disconnect(): Closes the WebSocket connection to the IB server.
        is_connected(): Checks if the client is currently connected to the IB server.
        get_data(data_type, contract): Requests data for the specified market data type and contract.
        stream_5_sec_bars(contract): Initiates a 5-second bar data stream for a given contract.
        cancel_all_bar_data(): Cancels all active 5-second bar data streams.
        stream_quote_data(contract): Starts streaming quote data for a given contract.
        cancel_all_quote_data(): Cancels all active quote data streams.
    """

    def __init__(self, symbols_map: SymbolMap, bus: MessageBus, **kwargs):
        """
        Initializes the DataClient instance.

        Args:
            config (Config): Configuration object containing data source and strategy parameters.
            symbols_map (SymbolMap): Mapping of symbols to instrument IDs.
        """
        super().__init__(symbols_map, bus)

        self.logger = SystemLogger.get_logger()
        self.app = DataApp(bus, kwargs["tick_interval"])
        self.data_type = LiveDataType[kwargs["data_type"].upper()]
        self.host = kwargs["host"]
        self.port = int(kwargs["port"])
        self.clientId = kwargs["client_id"]
        self.account = kwargs["account_id"]
        self.lock = threading.Lock()  # create a lock

        self.validated_contracts = {}

    # -- Helper --
    def _websocket_connection(self) -> None:
        """
        Internal method to manage the WebSocket connection lifecycle.
        """
        self.app.connect(self.host, self.port, self.clientId)
        self.app.run()

    def _get_valid_id(self) -> int:
        """
        Retrieves and increments the next valid order ID in a thread-safe manner.

        Returns:
            int: The next available valid order ID for use in requests.
        """
        with self.lock:
            current_valid_id = self.app.next_valid_order_id
            self.app.next_valid_order_id += 1
            return current_valid_id

    def process(self):
        # self.connect()
        thread = threading.Thread(
            target=self._websocket_connection, daemon=True
        )
        thread.start()

        # Waiting for confirmation of connection
        self.logger.info("Waiting For Data Connection...")
        self.app.connected_event.wait()

        #  Waiting for next valid id to be returned
        self.app.valid_id_event.wait()

        self._load_live_data()

        self.logger.info("IBDataAdaptor running ...")
        self.running.set()

        while not self.shutdown_event.is_set():
            continue

        self.cleanup()

    def cleanup(self):
        """
        Main processing loop that streams data and handles EOD synchronization.
        """
        self.logger.info("Data Engine - stream done")

    # -- Connection --
    def connect(self) -> None:
        """
        Establishes a WebSocket connection to the IB server and waits for confirmation.

        This method starts a new thread to establish the connection and ensures that the next valid order ID
        is initialized before proceeding.
        """
        thread = threading.Thread(
            target=self._websocket_connection, daemon=True
        )
        thread.start()

        # Waiting for confirmation of connection
        self.logger.info("Waiting For Data Connection...")
        self.app.connected_event.wait()

        #  Waiting for next valid id to be returned
        self.app.valid_id_event.wait()

    def disconnect(self) -> None:
        """
        Closes the WebSocket connection to the IB server.
        """
        self.app.disconnect()

    def is_connected(self) -> bool:
        """
        Checks if the client is connected to the broker's API.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self.app.isConnected()

    # -- Data --
    def _load_live_data(self):
        """
        Subscribe to live data feeds for the trading symbols.

        Raises:
            ValueError: If live data fails to load for any symbol.
        """
        try:
            for symbol in self.symbols_map.symbols:
                self.get_data(
                    data_type=self.data_type,
                    contract=symbol.contract,
                )
        except ValueError:
            raise ValueError(f"Error loading live data for {symbol.ticker}.")

    def get_data(self, data_type: LiveDataType, contract: Contract) -> None:
        """
        Requests data for the specified market data type and financial contract.

        Args:
            data_type (LiveDataType): The type of market data to request (e.g., TICK, BAR).
            contract (Contract): The financial contract for which data is requested.

        Raises:
            ValueError: If an unsupported data type is specified.
        """
        if data_type == LiveDataType.TICK:
            self.stream_quote_data(contract)
        elif data_type == LiveDataType.BAR:
            self.stream_5_sec_bars(contract)
        else:
            raise ValueError(
                "'data_type' must be of type MarketDataType enum."
            )

    def stream_5_sec_bars(self, contract: Contract) -> None:
        """
        Initiates a 5-second bar data stream for the specified contract.

        Args:
            contract (Contract): The financial contract for which 5-second bars are requested.
        """
        reqId = self._get_valid_id()
        instrument_id = self.symbols_map.get_id(contract.symbol)

        # TODO: may not need the reqId check
        if (
            reqId not in self.app.reqId_to_instrument.keys()
            and instrument_id not in self.app.reqId_to_instrument.values()
        ):
            self.app.reqRealTimeBars(
                reqId=reqId,
                contract=contract,
                barSize=5,
                whatToShow="TRADES",
                useRTH=False,
                realTimeBarsOptions=[],
            )
            self.app.reqId_to_instrument[reqId] = instrument_id
            self.logger.info(f"Started 5 sec bar data stream for {contract}.")
        else:
            self.logger.error(
                f"Data stream already established for {contract}."
            )

    def cancel_all_bar_data(self) -> None:
        """
        Cancels all active 5-second bar data streams and clears related mappings.
        """
        # Cancel real time bars for all reqId ** May not all be on bar data **
        for reqId in self.app.reqId_to_instrument.keys():
            self.app.cancelRealTimeBars(reqId)
        self.app.reqId_to_instrument.clear()

    def stream_quote_data(self, contract: Contract) -> None:
        """
        Starts a real-time quote data stream for the specified contract.

        Args:
            contract (Contract): The financial contract for which quote data is requested.
        """
        reqId = self._get_valid_id()
        instrument_id = self.symbols_map.get_id(contract.symbol)

        if (
            reqId not in self.app.reqId_to_instrument.keys()
            and instrument_id not in self.app.reqId_to_instrument.values()
        ):
            self.app.reqMktData(
                reqId=reqId,
                contract=contract,
                genericTickList="",
                snapshot=False,
                regulatorySnapshot=False,
                mktDataOptions=[],
            )
            self.app.reqId_to_instrument[reqId] = instrument_id
            bbo_obj = BboMsg(
                instrument_id=instrument_id,
                ts_event=0,
                price=0,
                size=0,
                side=Side.NONE,
                flags=0,
                ts_recv=0,
                sequence=0,
                levels=[
                    BidAskPair(
                        bid_px=0,
                        ask_px=0,
                        bid_sz=0,
                        ask_sz=0,
                        bid_ct=0,
                        ask_ct=0,
                    )
                ],
            )
            self.app.tick_data[reqId] = bbo_obj
            self.logger.info(f"Requested top of book stream for {contract}.")

        self.logger.error(f"Data stream already established for {contract}.")

    def cancel_all_quote_data(self) -> None:
        """
        Cancels all active quote data streams and clears associated mappings.
        """
        # Cancel real tiem bars for all reqId ** May not all be on bar data **
        for reqId in self.app.reqId_to_instrument.keys():
            self.app.cancelMktData(reqId)

        self.app.reqId_to_instrument.clear()

    # def cancel_market_data_stream(self,contract:Contract):
    #     for key, value in self.app.market_data_top_book.items():
    #         if value['CONTRACT'] == contract:
    #             self.app.cancelMktData(reqId=key)
    #             remove_key = key
    #     del self.app.market_data_top_book[key]

    # def get_top_book_market_data(self):
    #     return self.app.market_data_top_book

    # -- Contract Validation --
    def validate_contract(self, contract: Contract) -> bool:
        """
        Validates a contract with Interactive Brokers.

        Behavior:
            - Checks if the contract is already validated.
            - If not validated, sends a request to Interactive Brokers for validation.
            - Updates `validated_contracts` upon successful validation.

        Args:
            contract (Contract): The `Contract` object to be validated.

        Returns:
            bool: `True` if the contract is successfully validated, otherwise `False`.

        Raises:
            ValueError: If the provided `contract` is not an instance of `Contract`.
        """
        if not isinstance(contract, Contract):
            raise ValueError("'contract' must be of type Contract instance.")

        # Check if the contract is already validated
        if self._is_contract_validated(contract):
            self.logger.info(f"Contract {contract.symbol} already validated.")
            return True

        # Reset the validation attribute in case it has been used before
        self.app.is_valid_contract = None
        self.app.validate_contract_event.clear()

        # Request contract details from IB
        reqId = self._get_valid_id()
        self.app.reqContractDetails(reqId=reqId, contract=contract)
        self.app.validate_contract_event.wait()

        # Store the validated contract if it's valid
        if self.app.is_valid_contract:
            self.validated_contracts[contract.symbol] = contract
            self.logger.info(
                f"Contract {contract.symbol} validated successfully."
            )
        else:
            self.logger.warning(
                f"Contract {contract.symbol} validation failed."
            )

        return self.app.is_valid_contract

    def _is_contract_validated(self, contract: Contract) -> bool:
        """
        Checks if a contract has already been validated.

        Args:
            contract (Contract): The `Contract` object to check for validation.

        Returns:
            bool: `True` if the contract has already been validated, otherwise `False`.
        """
        return contract.symbol in self.validated_contracts

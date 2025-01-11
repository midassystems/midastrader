import queue
import threading
from typing import Dict
from threading import Lock
from typing import Optional

from midastrader.structs.account import Account
from midastrader.structs.positions import Position
from midastrader.structs.active_orders import ActiveOrder
from midastrader.utils.logger import SystemLogger
from midastrader.structs.symbol import SymbolMap
from midastrader.message_bus import MessageBus, EventType
from midastrader.core.adapters.base import CoreAdapter
from .managers import AccountManager, OrderManager, PositionManager


class PortfolioServer:
    """
    Manages and updates the state of the portfolio, including positions, orders, and account details.

    The `PortfolioServer` class acts as both a subject and an observer, handling updates to the portfolio
    and notifying observers of any changes. It integrates with position, order, and account managers to
    ensure accurate state management and provides utility methods for accessing portfolio details.

    Attributes:
        logger (SystemLogger): Logger instance for recording system events.
        order_manager (OrderManager): Manages the state and updates of orders.
        position_manager (PositionManager): Tracks and updates portfolio positions.
        account_manager (AccountManager): Manages account details such as capital and account metrics.
        symbols_map (SymbolMap): A mapping of symbol strings to `Symbol` objects for portfolio instruments.
    """

    _instance: Optional["PortfolioServer"] = None
    _lock: Lock = Lock()  # For thread-safe singleton initialization

    def __init__(self):
        """
        Initializes a new instance of the PortfolioServer.

        Parameters:
            symbols_map (SymbolMap): Mapping of symbol strings to `Symbol` objects for instruments.
        """
        if PortfolioServer._instance is not None:
            raise Exception(
                "PortfolioServer is a singleton. Use get_instance() to access."
            )
        self.logger = SystemLogger.get_logger()
        self.order_manager = OrderManager(self.logger)
        self.position_manager = PositionManager(self.logger)
        self.account_manager = AccountManager(self.logger)
        self._read_lock = Lock()  # Lock for thread-safe reads

    @staticmethod
    def get_instance() -> "PortfolioServer":
        with PortfolioServer._lock:
            if PortfolioServer._instance is None:
                PortfolioServer._instance = PortfolioServer()
        return PortfolioServer._instance

    @property
    def capital(self) -> float:
        """
        Retrieves the available capital from the account.

        Returns:
            float: The current available capital.
        """
        with self._read_lock:
            return self.account_manager.get_capital

    @property
    def positions(self) -> Dict[int, Position]:
        """
        Retrieves the current positions in the portfolio.

        Returns:
            Dict[int, Position]: A dictionary of current positions keyed by instrument ID.
        """
        with self._read_lock:
            return self.position_manager.get_positions

    @property
    def account(self) -> Account:
        """
        Retrieves the account details of the portfolio.

        Returns:
            Account: The current account object.
        """
        with self._read_lock:
            return self.account_manager.account

    @property
    def active_orders(self) -> Dict[int, ActiveOrder]:
        """
        Retrieves the active orders in the portfolio.

        Returns:
            Dict[int, ActiveOrder]: A dictionary of active orders keyed by order ID.
        """
        with self._read_lock:
            return self.order_manager.active_orders

    def get_active_order_tickers(self) -> list:
        """
        Retrieves a list of tickers that currently have active orders.

        Returns:
            List[str]: A list of tickers with active orders.
        """
        with self._read_lock:
            return self.order_manager.get_active_order_tickers()


class PortfolioServerManager(CoreAdapter):
    """
    Responsible for updating the portfolio state.

    The `PortfolioManager` acts as the sole writer for the `PortfolioServer`, ensuring all updates are
    controlled and consistent.
    """

    def __init__(self, symbols_map: SymbolMap, bus: MessageBus):
        super().__init__(symbols_map, bus)
        self.server = PortfolioServer.get_instance()
        self.threads = []
        self.running = threading.Event()

        # Subscribe to events
        self.order_queue = self.bus.subscribe(EventType.ORDER_UPDATE)
        self.position_queue = self.bus.subscribe(EventType.POSITION_UPDATE)
        self.account_queue = self.bus.subscribe(EventType.ACCOUNT_UPDATE)

    def process(self):
        # Start sub-threads
        try:
            self.threads.append(
                threading.Thread(target=self.process_orders, daemon=True)
            )
            self.threads.append(
                threading.Thread(target=self.process_positions, daemon=True)
            )
            self.threads.append(
                threading.Thread(target=self.process_account, daemon=True)
            )

            for thread in self.threads:
                thread.start()

            self.logger.info("Porfolioserver running ...")
            self.running.set()

            for thread in self.threads:
                thread.join()

        finally:
            self.cleanup()

    def cleanup(self) -> None:
        self.logger.info("Shutting down portfolio server manager...")

    def process_orders(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        while not self.shutdown_event.is_set():
            try:
                item = self.order_queue.get()
                self.server.order_manager.update_orders(item)
            except queue.Empty:
                continue

    def process_positions(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        while not self.shutdown_event.is_set():
            try:
                item = self.position_queue.get()
                self.server.position_manager.update_positions(item[0], item[1])
            except queue.Empty:
                continue

    def process_account(self) -> None:
        """
        Continuously processes market data events in a loop.

        This function runs as the main loop for the `OrderBook` to handle
        incoming market data messages from the `MessageBus`.
        """
        while not self.shutdown_event.is_set():
            try:
                item = self.account_queue.get()
                self.server.account_manager.update_account_details(item)
            except queue.Empty:
                continue

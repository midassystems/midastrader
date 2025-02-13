import queue
import threading

from midastrader.execution.adaptors.dummy.dummy_broker import DummyBroker
from midastrader.message_bus import MessageBus, EventType
from midastrader.structs.symbol import SymbolMap
from midastrader.execution.adaptors.base import ExecutionAdapter


class DummyAdaptor(ExecutionAdapter):
    """
    Simulates the execution of trades and updates account data.

    This class acts as an intermediary between the trading strategy and the actual or simulated market, handling
    order execution, tracking trades, and updating account and position data based on trade outcomes.

    Attributes:
        broker (DummyBroker): Simulates broker functionalities for executing trades and managing account details.
        symbols_map (SymbolMap): Maps symbols to unique identifiers for instruments.
        logger (logging.Logger): Logger for tracking and reporting system operations.
    """

    def __init__(self, symbols_map: SymbolMap, bus: MessageBus, capital: int):
        """
        Initializes a BrokerClient with the necessary components to simulate broker functionalities.

        Args:
            broker (DummyBroker): The simulated broker backend for order execution and account management.
            symbols_map (SymbolMap): Mapping of symbols to unique identifiers for instruments.
        """
        super().__init__(symbols_map, bus)
        self.threads = []
        self.broker = DummyBroker(self.symbols_map, self.bus, capital)

        # Subscriptions
        self.order_queue = self.bus.subscribe(EventType.ORDER)

    def process(self) -> None:
        self.threads.append(
            threading.Thread(target=self.process_orders, daemon=True)
        )
        self.threads.append(
            threading.Thread(target=self.broker.process, daemon=True)
        )

        for thread in self.threads:
            thread.start()

        self.broker.is_running.wait()

        self.logger.info("DummyBrokerAdaptor running ...")
        self.is_running.set()

        for thread in self.threads:
            thread.join()

        self.logger.info("Shutting down DummyBrokerAdaptor ...")
        self.is_shutdown.set()

    def process_orders(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                order = self.order_queue.get(timeout=0.01)
                self.logger.debug(order)
                self.bus.publish(EventType.TRADE, order)
            except queue.Empty:
                continue

        self.cleanup()

    def cleanup(self) -> None:
        while True:
            try:
                order = self.order_queue.get(timeout=1)
                self.logger.debug(order)
                self.bus.publish(EventType.TRADE, order)
            except queue.Empty:
                break

        self.broker.shutdown_event.set()
        self.broker.is_shutdown.wait()

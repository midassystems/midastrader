import threading

from midas.core.order_book import OrderBookManager
from midas.core.portfolio import PortfolioServerManager
from midas.core.order_manager import OrderExecutionManager
from midas.core.performance.base import PerformanceManager
from midas.config import Parameters, Mode
from midas.core.base_strategy import BaseStrategy
from midas.core.risk.risk_handler import RiskHandler
from midas.structs.symbol import SymbolMap
from midas.utils.logger import SystemLogger
from midas.message_bus import MessageBus, EventType


class CoreEngine:
    def __init__(
        self,
        symbols_map: SymbolMap,
        message_bus: MessageBus,
        mode: Mode,
        params: Parameters,
        output_dir: str,
    ):
        self.logger = SystemLogger.get_logger()
        self.mode = mode
        self.params = params
        self.message_bus = message_bus
        self.symbols_map = symbols_map
        self.output_dir = output_dir

        self.porfolio_manager = None
        self.orderbook_manager = None
        self.performance_manager = None
        self.order_manager = None
        self.threads = []

    def initialize(self):
        """
        Create the core components of the trading system:
        - OrderBook: Manages market data and order book updates.
        - PortfolioServer: Tracks positions and account updates.
        - OrderExecutionManager: Handles order execution.
        - PerformanceManager: Tracks system performance.

        Returns:
            EngineBuilder: Returns the current instance for method chaining.
        """

        self.orderbook_manager = OrderBookManager(
            self.symbols_map,
            self.message_bus,
            self.mode,
        )
        self.threads.append(
            threading.Thread(
                target=self.orderbook_manager.process,
                daemon=True,
            )
        )

        self.porfolio_manager = PortfolioServerManager(
            self.symbols_map,
            self.message_bus,
        )
        self.threads.append(
            threading.Thread(
                target=self.porfolio_manager.process,
                daemon=True,
            )
        )

        self.order_manager = OrderExecutionManager(
            self.symbols_map,
            self.message_bus,
        )
        self.threads.append(
            threading.Thread(
                target=self.order_manager.process,
                daemon=True,
            )
        )

        self.performance_manager = PerformanceManager(
            self.symbols_map,
            self.message_bus,
            self.params,
            self.mode,
            self.output_dir,
        )
        self.threads.append(
            threading.Thread(
                target=self.performance_manager.process,
                daemon=True,
            )
        )

        return self

    def set_risk_model(self):
        """
        Initialize and set the risk model for the trading system.

        Attaches the risk model to the database observer to track risk updates.
        """
        return

        # if self.config.risk_class:
        #     self.risk_model = RiskHandler(self.config.risk_class)
        #
        #     # Attach the DatabaseUpdater as an observer to RiskModel
        #     self.risk_model.attach(
        #         self.observer,
        #         EventType.RISK_MODEL_UPDATE,
        #     )

    def set_strategy(self, strategy_class: BaseStrategy):
        """
        Load and initialize the trading strategy.

        Attaches the strategy to key components such as the order book, order manager, and performance manager.
        """
        self.strategy = strategy_class(self.symbols_map, self.message_bus)
        self.threads.append(
            threading.Thread(
                target=self.strategy.process,
                daemon=True,
            )
        )
        self.performance_manager.set_strategy(self.strategy)

    def start(self):
        """Start adapters in seperate threads."""

        for thread in self.threads:
            thread.start()

        # Start a monitoring thread to check when all adapter threads are done
        threading.Thread(target=self._monitor_threads, daemon=True).start()

    def _monitor_threads(self):
        """
        Monitor all adapter threads and signal when all are done.
        """
        for thread in self.threads:
            thread.join()  # Wait for each thread to finish

        self.logger.info("All adapter threads have completed.")
        self.completed.set()  # Signal that the DataEngine is done

    def wait_until_complete(self):
        """
        Wait for the engine to complete processing.
        """
        self.completed.wait()  # Block until the completed event is set

    def stop(self):
        """Start adapters in separate threads."""
        self.logger.info("Core Engine -  Shutting down DataEngine...")
        self.performance_manager.save()

        self.orderbook_manager.shutdown_event.set()
        self.order_manager.shutdown_event.set()
        self.porfolio_manager.shutdown_event.set()
        self.performance_manager.shutdown_event.set()
        self.strategy.shutdown_event.set()

import threading

from midastrader.config import Parameters, Mode
from midastrader.structs.symbol import SymbolMap
from midastrader.utils.logger import SystemLogger
from midastrader.message_bus import MessageBus
from midastrader.core.adapters import (
    BaseStrategy,
    OrderExecutionManager,
    OrderBookManager,
    PortfolioServerManager,
    PerformanceManager,
)

# from midastrader.core.adapters.risk import RiskHandler


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
        self.adapters = {}

        self.porfolio_manager = None
        self.orderbook_manager = None
        self.performance_manager = None
        self.order_manager = None
        self.threads = []

        self.running = threading.Event()
        self.completed = threading.Event()

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

        self.adapters["order_book"] = OrderBookManager(
            self.symbols_map,
            self.message_bus,
            self.mode,
        )

        self.adapters["portfolio_server"] = PortfolioServerManager(
            self.symbols_map,
            self.message_bus,
        )

        self.adapters["order_manager"] = OrderExecutionManager(
            self.symbols_map,
            self.message_bus,
        )

        self.adapters["performance_manager"] = PerformanceManager(
            self.symbols_map,
            self.message_bus,
            self.params,
            self.mode,
            self.output_dir,
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

    def set_strategy(self, strategy: BaseStrategy):
        """
        Load and initialize the trading strategy.

        Attaches the strategy to key components such as the order book, order manager, and performance manager.
        """
        if not isinstance(strategy, BaseStrategy):
            raise TypeError("Strategy must be an instance of BaseStrategy")
        # self._strategy = value

        self.adapters["strategy"] = strategy
        # strategy(
        #     self.symbols_map,
        #     self.message_bus,
        # )

        self.adapters["performance_manager"].set_strategy(
            self.adapters["strategy"]
        )

    def start(self):
        """Start adapters in seperate threads."""
        self.logger.info("Core-engine starting ...")

        for adapter in self.adapters.values():
            thread = threading.Thread(target=adapter.process, daemon=True)
            self.threads.append(thread)  # Keep track of threads
            thread.start()
            adapter.is_running.wait()

        # Start a monitoring thread to check when all adapter threads are done
        threading.Thread(target=self._monitor_threads, daemon=True).start()
        self.logger.info("Core-engine running ...\n")
        self.running.set()

    def _monitor_threads(self):
        """
        Monitor all adapter threads and signal when all are done.
        """
        for thread in self.threads:
            thread.join()  # Wait for each thread to finish

        self.logger.info("CoreEngine threads completed, shutting down ...")
        self.completed.set()  # Signal that the DataEngine is done

    def wait_until_complete(self):
        """
        Wait for the engine to complete processing.
        """
        self.completed.wait()  # Block until the completed event is set

    def stop(self):
        """Start adapters in separate threads."""

        # Shutdown OrderBookManager
        self.adapters["order_book"].shutdown_event.set()
        self.adapters["order_book"].is_shutdown.wait()

        # Shutdown strategy
        # self.adapters["strategy"].shutdown_event.set()
        # self.adapters["strategy"].is_shutdown.wait()

        # Shutdown OrderExecutionManager
        self.adapters["order_manager"].shutdown_event.set()
        self.adapters["order_manager"].is_shutdown.wait()

        # self.logger.info("Shutting down CoreEngine main components ...")
        # self.adapters["performance_manager"].save()
        # self.adapters["portfolio_server"].shutdown_event.set()
        # self.adapters["performance_manager"].shutdown_event.set()

    def save(self):
        """Start adapters in separate threads."""
        # Shutdown performance manaer
        # self.adapters["performance_manager"].save()
        self.adapters["performance_manager"].shutdown_event.set()
        self.adapters["performance_manager"].is_shutdown.wait()

        # Shutdown portfolio server
        self.adapters["portfolio_server"].shutdown_event.set()
        self.adapters["portfolio_server"].is_shutdown.wait()

        self.adapters["strategy"].shutdown_event.set()
        self.adapters["strategy"].is_shutdown.wait()

        # self.logger.info("Shutting down CoreEngine components ...")

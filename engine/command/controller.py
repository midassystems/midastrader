import time
import signal

from .config import Config, Mode
from engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent, EODEvent

class EventController:
    """
    Controls the event-driven mechanisms of the trading system, handling both live and backtest modes.

    This controller manages the event queue and dispatches events to appropriate components within the trading system,
    such as strategies, performance managers, and brokers. It ensures that each event type triggers the correct processes
    and handles both the normal operation and termination of the trading session.

    Attributes:
    - event_queue (queue.Queue): The queue from which the system processes events.
    - mode (Mode): The operational mode of the trading session (LIVE or BACKTEST).
    - hist_data_client (DataClient): Client responsible for historical data during backtests.
    - broker_client (BrokerClient): Client that manages interactions with the brokerage.
    - strategy (BaseStrategy): The trading strategy in use.
    - order_manager (OrderManager): Manages the execution and lifecycle of orders.
    - performance_manager (BasePerformanceManager): Handles performance measurement and reporting.
    - database_updater (DatabaseUpdater): Manages updates to the database in response to system events.
    - logger (logging.Logger): Provides logging capabilities across the trading system.

    Methods:
    - run(): Starts the event processing loop depending on the mode.
    - signal_handler(signum, frame): Handles signals for graceful shutdown.
    - _run_live(): Processes events for live trading sessions.
    - _run_backtest(): Processes events for backtesting sessions.
    """
    def __init__(self, config:Config):
        # Initialize instance variables
        self.event_queue = config.event_queue
        self.mode = config.mode
        
        # Gateways
        self.hist_data_client = config.hist_data_client
        self.broker_client = config.broker_client
        
        # Core Components
        self.strategy = config.strategy
        self.order_manager = config.order_manager

        # Supporting Components
        self.performance_manager = config.performance_manager
        self.database_updater = config.db_updater
        self.logger = config.logger
        
    def run(self):
        """
        Initiates the processing of events based on the trading mode.

        Depending on the configuration, this method starts the event processing for either live trading or backtesting.
        It handles the main loop of event processing, dispatching to specific routines for live or backtest modes.
        """
        if self.mode == Mode.LIVE:
            self._run_live()
        elif self.mode == Mode.BACKTEST:
            self._run_backtest()

    def signal_handler(self, signum, frame):
        """
        This method is triggered by signals like SIGINT, allowing the system to perform cleanup and save state
        before a complete shutdown.

        Parameters:
        - signum (int): The signal number.
        - frame (Frame): The current stack frame (not used in this handler).
        """
        self.logger.info("Signal received, preparing to shut down.")
        self.running = False  # Clear the flag to stop the loop
  
    def _run_live(self):
        """
        Manages the event loop for live trading sessions.

        This method continuously processes events from the event queue during a live session, handling different types
        of events such as market data, signals, orders, and execution updates. It ensures that all components are
        appropriately updated and that the system can handle user-initiated or system signals for stopping the trading.
        """
        self.running = True  # Flag to control the loop
        signal.signal(signal.SIGINT, self.signal_handler)  # Register signal handler
        while self.running:
            while not self.event_queue.empty():
                event = self.event_queue.get()
                self.logger.info(event)

                if isinstance(event, MarketEvent):
                    self.strategy.handle_market_data()

                elif isinstance(event, SignalEvent):
                    self.performance_manager.update_signals(event)
                    self.order_manager.on_signal(event)

                elif isinstance(event, OrderEvent):
                    self.broker_client.on_order(event)

        # Perform cleanup here
        self.logger.info("Live trading stopped. Performing cleanup...")
        self.database_updater.delete_session()
        
        # Finalize and save to database
        self.broker_client.request_account_summary()
        time.sleep(5) # buffer to allow time for final account summary request (could possibly be shorter)
        self.performance_manager.save()

    def _run_backtest(self):
        """
        Manages the event loop for backtesting sessions.

        Processes all events that simulate the market conditions during a backtest. This involves responding to
        market, signal, order, execution, and end-of-day events, allowing the system to emulate a live trading
        environment using historical data.

        It ensures that all trading activities are recorded and analyzed, with final results calculated and saved.
        """
        while self.hist_data_client.data_stream():
            while not self.event_queue.empty():
                event = self.event_queue.get()
                self.logger.info(event)

                if isinstance(event, MarketEvent):
                    self.broker_client.update_equity_value() # Updates equity value of the account with every new price change
                    self.strategy.handle_market_data()

                elif isinstance(event, SignalEvent):
                    self.performance_manager.update_signals(event)
                    self.order_manager.on_signal(event)

                elif isinstance(event, OrderEvent):
                    self.broker_client.on_order(event)

                elif isinstance(event, ExecutionEvent):
                    self.broker_client.on_execution(event)

                elif isinstance(event, EODEvent):
                    self.broker_client.eod_update()
        
        # Perform cleanup here
        self.logger.info("Backtest complete. Finalizing results ...")
       
        # Perform EOD operations for the last trading day
        self.broker_client.eod_update()
        self.broker_client.liquidate_positions()
        
        # Finalize and save to database
        self.performance_manager.calculate_statistics() 
        self.performance_manager.save()

import time
import signal

from .config import Config, Mode
from engine.events import MarketEvent, OrderEvent, SignalEvent, ExecutionEvent, EODEvent

class EventController:
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
        if self.mode == Mode.LIVE:
            self._run_live()
        elif self.mode == Mode.BACKTEST:
            self._run_backtest()

    def signal_handler(self, signum, frame):
        """Handles termination signals to allow for a graceful shutdown."""
        self.logger.info("Signal received, preparing to shut down.")
        self.running = False  # Clear the flag to stop the loop
  
    def _run_live(self):
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
        time.sleep(5)
        # self.performance_manager.calculate_statistics()
        self.performance_manager.create_live_session()

    def _run_backtest(self):
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
        self.performance_manager.calculate_statistics() ## -- check point --
        self.performance_manager.create_backtest()

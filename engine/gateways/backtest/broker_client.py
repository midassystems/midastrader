import logging
from queue import Queue
from ibapi.contract import Contract

from .dummy_broker import DummyBroker
from engine.events import ExecutionEvent
from engine.portfolio import PortfolioServer
from engine.performance import BasePerformanceManager
from engine.events import ExecutionEvent, OrderEvent

from shared.trade import Trade
from shared.portfolio import Position
from shared.orders import Action, BaseOrder

class BrokerClient:
    """
    Simulates the execution of trades and updating account data.

    This class acts as an intermediary between the trading strategy and the actual or simulated market, handling
    order execution, tracking trades, and updating account and position data based on trade outcomes.

    Attributes:
    - event_queue (Queue): A queue for handling events such as orders and executions.
    - logger (logging.Logger): Logger for tracking and reporting system operations.
    - portfolio_server (PortfolioServer): Manages and updates the portfolio based on trading activities.
    - performance_manager (BasePerformanceManager): Tracks and reports on trading performance.
    - broker (DummyBroker): Simulates broker functionalities for executing trades and managing account details.

    Methods:
    - on_order(event: OrderEvent): Processes new order events, initiating trade execution.
    - handle_order(timestamp, trade_id, leg_id, action, contract, order): Executes orders based on trading signals and market data.
    - on_execution(event: ExecutionEvent): Handles execution events, updating system state based on trade outcomes.
    - eod_update(): Performs end-of-day updates such as marking positions to market and checking margin requirements.
    - update_positions(): Retrieves and updates position data from the broker simulation.
    - update_trades(contract=None): Retrieves and updates trade execution details.
    - update_account(): Fetches and updates account details like balance and margin.
    - update_equity_value(): Updates equity value based on current market valuations.
    - liquidate_positions(): Liquidates all positions at the end of a trading session or in response to market conditions.
    """
    def __init__(self,event_queue: Queue, logger: logging.Logger, portfolio_server: PortfolioServer, performance_manager: BasePerformanceManager, broker: DummyBroker):
        """
        Initializes a BrokerClient with the necessary components to simulate broker functionalities.

        Parameters:
        - event_queue (Queue): The event queue from which the broker receives trading events.
        - logger (logging.Logger): Logger for outputting system activities and errors.
        - portfolio_server (PortfolioServer): The component that manages portfolio state.
        - performance_manager (BasePerformanceManager): Manages and calculates performance metrics.
        - broker (DummyBroker): The simulated broker backend for order execution and account management.
        """
        # Subscriptions
        self.performance_manager = performance_manager
        self.portfolio_server = portfolio_server
        self.broker = broker
        self.logger = logger
        self.event_queue = event_queue

        self.update_account()
        
    def on_order(self, event: OrderEvent):
        """
        Handles new order events from the event queue and initiates order processing.

        Parameters:
        - event (OrderEvent): The event containing order details for execution.
        """
        if not isinstance(event,OrderEvent):
            raise ValueError("'event' must be of type OrderEvent instance.")
        
        timestamp = event.timestamp
        trade_id = event.trade_id
        leg_id = event.leg_id
        action = event.action
        contract = event.contract
        order = event.order

        self.handle_order(timestamp, trade_id, leg_id,action ,contract,order)

    def handle_order(self, timestamp: int, trade_id: int, leg_id: int, action: Action, contract: Contract, order: BaseOrder):
        """
        Directly processes and executes an order based on given details.

        Parameters:
        - timestamp (int): The UNIX timestamp of when the order was placed.
        - trade_id (int): Unique identifier for the trade.
        - leg_id (int): Identifier for a specific leg of a multi-leg order.
        - action (Action): The action type (BUY, SELL) of the order.
        - contract (Contract): The financial instrument involved in the order.
        - order (BaseOrder): The specific order details including type and quantity.
        """
        self.broker.placeOrder(timestamp, trade_id, leg_id, action ,contract, order)

    def on_execution(self, event: ExecutionEvent):
        """
        Responds to execution events, updating system states such as positions and account details.

        Parameters:
            event (ExecutionEvent): The event detailing the trade execution.
        """
        if not isinstance(event,ExecutionEvent):
            raise ValueError("'event' must be of type ExecutionEvent instance.")
        
        contract = event.contract
        
        self.update_positions()
        self.update_account()
        self.update_equity_value()
        self.update_trades(contract)
  
    def eod_update(self):
        """
        Performs end-of-day updates including marking positions to market values and checking margin requirements.

        This method is crucial for maintaining accurate account evaluations and ensuring compliance with trading regulations
        regarding margin requirements. It updates account and equity values based on the day's final prices.
        """
        self.broker.mark_to_market()
        self.broker.check_margin_call()
        self.update_account()
        self.update_equity_value()
   
    def update_positions(self):
        """
        Fetches and updates the positions from the broker and updates them in the portfolio server.

        This method retrieves the current positions held within the simulated broker, converts them into position data
        classes, and then updates the portfolio server with the latest position data. This keeps the portfolio records
        consistent with the simulated market conditions.
        """
        positions = self.broker.return_positions()
        for contract, position_data in positions.items():
            # Convert the `PositionDetails` TypedDict into a `Position` data class instance.
            position_instance = Position(
                action=position_data['action'],
                avg_cost=position_data['avg_cost'],
                quantity=position_data['quantity'],
                price_multiplier=position_data['price_multiplier'],
                quantity_multiplier=position_data['quantity_multiplier'],
                initial_margin=position_data['initial_margin'],
                total_cost=position_data.get('total_cost', 0),
                market_value=position_data.get('market_value', 0),   # Provide a default value if not present
            )

            # Now, use `position_instance` as needed, for example, to update positions in the portfolio server.
            self.portfolio_server.update_positions(contract, position_instance)

    def update_trades(self, contract: Contract = None):
        """
        Updates the trade details in the performance manager either for a specific contract or for all recent trades.

        Parameters:
        - contract (Contract, optional): Specific contract for which trades need to be updated. If None, updates all recent trades.

        This method retrieves last executed trades either for a specific contract or for all contracts from the broker and then
        updates the performance manager with these trades to ensure accurate performance tracking and reporting.
        """
        if contract:
            trade = self.broker.return_executed_trades(contract)
            self.performance_manager.update_trades(Trade(
                                                        trade_id = trade['trade_id'],
                                                        leg_id = trade['leg_id'],
                                                        timestamp = trade['timestamp'],
                                                        ticker = trade['symbol'],
                                                        quantity = trade['quantity'],
                                                        price =  round(trade['price'],4),
                                                        cost = trade['cost'],
                                                        action = trade['action'],
                                                        fees = trade['fees']
                                                    ))
        else: 
            last_trades = self.broker.return_executed_trades()
            for contract, trade in last_trades.items():
                self.performance_manager.update_trades(Trade(
                                                        trade_id = trade['trade_id'],
                                                        leg_id = trade['leg_id'],
                                                        timestamp = trade['timestamp'],
                                                        ticker = trade['symbol'],
                                                        quantity = trade['quantity'],
                                                        price =  round(trade['price'],4),
                                                        cost = trade['cost'],
                                                        action = trade['action'],
                                                        fees = trade['fees']
                                                    ))

    def update_account(self):
        """
        Retrieves and updates the account details from the broker into the portfolio server.

        This method synchronizes the account state with the broker's state, ensuring that the portfolio server has the most
        current information regarding account balances and other financial metrics.
        """
        account = self.broker.return_account()
        self.portfolio_server.update_account_details(account)

    def update_equity_value(self):
        """
        Updates the equity value of the account based on the latest market valuations.

        This method is essential for reflecting the current market value of the account's holdings, adjusting for market movements
        and trading activities throughout the trading day.
        """
        self.broker._update_account_equity_value() 
        equity = self.broker.return_equity_value()
        self.performance_manager.update_equity(equity)
       
    def liquidate_positions(self):
        """
        Handles the liquidation of all positions, typically used at the end of a trading period or in response to a margin call.

        This method ensures that all positions are closed out, the account is updated, and performance calculations can be finalized.
        It is an essential step in preparing the account for closure or for the next trading period.
        """
        self.update_positions()
        self.update_account()
        self.update_equity_value()
        self.broker.liquidate_positions()
        self.update_trades()
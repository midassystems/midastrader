from ibapi.contract import Contract
from midas.utils.logger import SystemLogger
from midas.engine.components.gateways.base import BaseBrokerClient
from midas.engine.events import (
    ExecutionEvent,
    OrderEvent,
    EODEvent,
    MarketEvent,
)
from midas.engine.components.gateways.backtest.dummy_broker import DummyBroker
from midas.engine.components.observer.base import Observer, Subject, EventType
from midas.symbol import SymbolMap


class BrokerClient(Subject, Observer, BaseBrokerClient):
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

    def __init__(self, broker: DummyBroker, symbols_map: SymbolMap):
        """
        Initializes a BrokerClient with the necessary components to simulate broker functionalities.

        Parameters:
        - event_queue (Queue): The event queue from which the broker receives trading events.
        - logger (logging.Logger): Logger for outputting system activities and errors.
        - portfolio_server (PortfolioServer): The component that manages portfolio state.
        - performance_manager (BasePerformanceManager): Manages and calculates performance metrics.
        - broker (DummyBroker): The simulated broker backend for order execution and account management.
        """
        Subject.__init__(self)
        self.broker = broker
        self.symbols_map = symbols_map
        self.logger = SystemLogger.get_logger()

    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        event,
    ) -> None:
        """
        Handles new order events from the event queue and initiates order processing.

        Parameters:
        - event (OrderEvent): The event containing order details for execution.
        """
        if event_type == EventType.ORDER_CREATED:
            if not isinstance(event, OrderEvent):
                raise ValueError(
                    "'event' must be of type OrderEvent instance."
                )
            self.handle_order(event)

        elif event_type == EventType.TRADE_EXECUTED:
            if not isinstance(event, ExecutionEvent):
                raise ValueError(
                    "'event' must be of type ExecutionEvent instance."
                )
            self.handle_execution(event)

        elif event_type == EventType.EOD_EVENT:
            if not isinstance(event, EODEvent):
                raise ValueError("'event' must be of type EODEvent.")

            self.handle_eod(event)

        elif event_type == EventType.ORDER_BOOK:
            if not isinstance(event, MarketEvent):
                raise ValueError("'event' must be of MarketEvent.")

            self.update_equity_value()

    def handle_order(self, event: OrderEvent):
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
        self.logger.debug(event)

        timestamp = event.timestamp
        trade_id = event.trade_id
        leg_id = event.leg_id
        action = event.action
        contract = event.contract
        order = event.order

        self.broker.placeOrder(
            timestamp,
            trade_id,
            leg_id,
            action,
            contract,
            order,
        )

    def handle_execution(self, event: ExecutionEvent):
        """
        Responds to execution events, updating system states such as positions and account details.

        Parameters:
            event (ExecutionEvent): The event detailing the trade execution.
        """
        self.logger.debug(event)

        # Update trades look with current event
        contract = event.contract
        self.update_trades(contract)

        # If last trade placed ex. only trade or last leg of a trade update data
        trade_details = event.trade_details
        if trade_details == self.broker.last_trade:
            self.update_positions()
            self.update_account()
            self.update_equity_value()

    def handle_eod(self, event: EODEvent):
        """
        Performs end-of-day updates including marking positions to market values and checking margin requirements.

        This method is crucial for maintaining accurate account evaluations and ensuring compliance with trading regulations
        regarding margin requirements. It updates account and equity values based on the day's final prices.
        """
        self.update_account()

    def update_positions(self):
        """
        Fetches and updates the positions from the broker and updates them in the portfolio server.

        This method retrieves the current positions held within the simulated broker, converts them into position data
        classes, and then updates the portfolio server with the latest position data. This keeps the portfolio records
        consistent with the simulated market conditions.
        """
        positions = self.broker.return_positions()
        for contract, position_data in positions.items():
            id = self.symbols_map.get_id(contract.symbol)
            self.notify(EventType.POSITION_UPDATE, id, position_data)

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
            trade_id = f"{trade.trade_id}{trade.leg_id}{trade.action}"
            self.notify(EventType.TRADE_UPDATE, trade_id, trade)
        else:
            last_trades = self.broker.return_executed_trades()
            for contract, trade in last_trades.items():
                trade_id = f"{trade.trade_id}{trade.leg_id}{trade.action}"
                self.notify(EventType.TRADE_UPDATE, trade_id, trade)

    def update_account(self):
        """
        Retrieves and updates the account details from the broker into the portfolio server.

        This method synchronizes the account state with the broker's state, ensuring that the portfolio server has the most
        current information regarding account balances and other financial metrics.
        """
        account = self.broker.return_account()
        self.notify(EventType.ACCOUNT_UPDATE, account)

    def update_equity_value(self):
        """
        Updates the equity value of the account based on the latest market valuations.

        This method is essential for reflecting the current market value of the account's holdings, adjusting for market movements
        and trading activities throughout the trading day.
        """
        self.broker._update_account()
        equity = self.broker.return_equity_value()
        self.notify(EventType.EQUITY_VALUE_UPDATE, equity)

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

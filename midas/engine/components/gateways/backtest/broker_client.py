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
    Simulates the execution of trades and updates account data.

    This class acts as an intermediary between the trading strategy and the actual or simulated market, handling
    order execution, tracking trades, and updating account and position data based on trade outcomes.

    Attributes:
        broker (DummyBroker): Simulates broker functionalities for executing trades and managing account details.
        symbols_map (SymbolMap): Maps symbols to unique identifiers for instruments.
        logger (logging.Logger): Logger for tracking and reporting system operations.
    """

    def __init__(self, broker: DummyBroker, symbols_map: SymbolMap):
        """
        Initializes a BrokerClient with the necessary components to simulate broker functionalities.

        Args:
            broker (DummyBroker): The simulated broker backend for order execution and account management.
            symbols_map (SymbolMap): Mapping of symbols to unique identifiers for instruments.
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
        Handles events from the event queue and initiates appropriate processing.

        Args:
            subject (Subject): The subject sending the event.
            event_type (EventType): The type of event being processed.
            event: The event object containing relevant details.

        Raises:
            ValueError: If the event is not of the expected type for the given event_type.
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

    def handle_order(self, event: OrderEvent) -> None:
        """
        Processes and executes an order based on given details.

        Args:
            event (OrderEvent): The event containing order details for execution.
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

    def handle_execution(self, event: ExecutionEvent) -> None:
        """
        Responds to execution events and updates system states such as positions and account details.

        Args:
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

    def handle_eod(self, event: EODEvent) -> None:
        """
        Performs end-of-day updates, including marking positions to market values and checking margin requirements.

        Args:
            event (EODEvent): The end-of-day event.
        """
        self.update_account()

    def update_positions(self) -> None:
        """
        Fetches and updates the positions from the broker and notifies observers of position updates.

        This method retrieves the current positions held within the simulated broker and updates the portfolio records
        to maintain consistency with the simulated market conditions.
        """
        positions = self.broker.return_positions()
        for contract, position_data in positions.items():
            id = self.symbols_map.get_id(contract.symbol)
            self.notify(EventType.POSITION_UPDATE, id, position_data)

    def update_trades(self, contract: Contract = None) -> None:
        """
        Updates trade details either for a specific contract or for all recent trades.

        Args:
            contract (Contract, optional): Specific contract for which trades need to be updated. If None, updates all recent trades.
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

    def update_account(self) -> None:
        """
        Retrieves and updates the account details from the broker.

        This method synchronizes the account state with the broker's state and notifies observers of the update.
        """
        account = self.broker.return_account()
        self.notify(EventType.ACCOUNT_UPDATE, account)

    def update_equity_value(self) -> None:
        """
        Updates the equity value of the account based on the latest market valuations.

        This method ensures the current market value of holdings is accurately reflected.
        """
        self.broker._update_account()
        equity = self.broker.return_equity_value()
        self.notify(EventType.EQUITY_VALUE_UPDATE, equity)

    def liquidate_positions(self) -> None:
        """
        Handles the liquidation of all positions, typically used at the end of a trading period or in response to a margin call.

        This method ensures all positions are closed out and the account is updated.
        """
        self.update_positions()
        self.update_account()
        self.update_equity_value()
        self.broker.liquidate_positions()
        self.update_trades()

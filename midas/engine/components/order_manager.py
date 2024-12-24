from ibapi.contract import Contract
from typing import List
from midas.symbol import SymbolMap
from midas.engine.components.order_book import OrderBook
from midas.signal import SignalInstruction
from midas.orders import Action, BaseOrder
from midas.engine.components.portfolio_server import PortfolioServer
from midas.engine.events import SignalEvent, OrderEvent
from midas.utils.logger import SystemLogger
from midas.engine.components.observer.base import Subject, Observer, EventType


class OrderExecutionManager(Subject, Observer):
    """
    Manages order execution based on trading signals.

    The `OrderExecutionManager` processes trading signals and initiates trade actions
    by interacting with the order book and portfolio server. It ensures that signals
    are validated against existing active orders and positions before executing any trades.
    """

    def __init__(
        self,
        symbols_map: SymbolMap,
        order_book: OrderBook,
        portfolio_server: PortfolioServer,
    ):
        """
        Initializes the OrderExecutionManager with required components.

        Args:
            symbols_map (SymbolMap): Mapping of symbol strings to `Symbol` objects.
            order_book (OrderBook): The order book reference for price lookups.
            portfolio_server (PortfolioServer): The portfolio server managing positions and account details.
        """
        super().__init__()
        self.logger = SystemLogger.get_logger()
        self.portfolio_server = portfolio_server
        self.order_book = order_book
        self.symbols_map = symbols_map

    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        event: SignalEvent,
    ) -> None:
        """
        Handles incoming signal events and initiates trade actions if applicable.

        Behavior:
            - Logs the received signal event.
            - Validates that no active orders exist for the tickers in the signal instructions.
            - Initiates trade execution by processing valid signal instructions.

        Args:
            subject (Subject): The subject sending the event.
            event_type (EventType): The type of event being handled. Expected: `EventType.SIGNAL`.
            event (SignalEvent): The signal event containing trade instructions.

        Raises:
            TypeError: If `event` is not an instance of `SignalEvent`.

        """
        if event_type == EventType.SIGNAL:
            self.logger.debug(event)
            if not isinstance(event, SignalEvent):
                raise TypeError("'event' must be SignalEvent.")

            trade_instructions = event.instructions
            timestamp = event.timestamp

            # Get a list of tickers in active orders
            active_orders_tickers = (
                self.portfolio_server.get_active_order_tickers()
            )
            self.logger.debug(f"Active order tickers {active_orders_tickers}")

            # Check if any of the tickers in trade_instructions are in active orders or positions
            if any(
                trade.instrument in active_orders_tickers
                for trade in trade_instructions
            ):
                self.logger.debug(
                    "One or more tickers in signal has active orders; ignoring signal."
                )
                return
            else:
                self._handle_signal(timestamp, trade_instructions)

    def _handle_signal(
        self,
        timestamp: int,
        trade_instructions: List[SignalInstruction],
    ) -> None:
        """
        Processes trade instructions and generates orders, ensuring sufficient capital is available.

        This method validates trading instructions, calculates capital requirements, and generates
        orders if capital constraints are satisfied.

        Behavior:
            - Calculates the total capital required for the orders.
            - Validates that sufficient capital is available for execution.
            - Queues orders for execution if constraints are met.
            - Logs a message if capital is insufficient.

        Args:
            timestamp (int): The time at which the signal was generated (UNIX nanoseconds).
            trade_instructions (List[SignalInstruction]): A list of trade instructions to process.

        """
        # Create and Validate Orders
        orders = []
        total_capital_required = 0

        for trade in trade_instructions:
            self.logger.debug(trade)
            symbol = self.symbols_map.map[trade.instrument]
            order = self._create_order(trade)
            current_price = self.order_book.retrieve(symbol.instrument_id)
            order_cost = symbol.cost(order.quantity, current_price)

            order_details = {
                "timestamp": timestamp,
                "trade_id": trade.trade_id,
                "leg_id": trade.leg_id,
                "action": trade.action,
                "contract": symbol.contract,
                "order": order,
            }

            orders.append(order_details)

            # SELL/Cover are exits so available capital will be freed up
            if trade.action not in [Action.SELL, Action.COVER]:
                total_capital_required += order_cost

        if total_capital_required <= self.portfolio_server.capital:
            for order in orders:
                # if (
                #     order["action"] in [Action.SELL, Action.COVER]
                #     or total_capital_required <= self.portfolio_server.capital
                # ):
                self._set_order(
                    order["timestamp"],
                    order["trade_id"],
                    order["leg_id"],
                    order["action"],
                    order["contract"],
                    order["order"],
                )
        else:
            self.logger.debug("Not enough capital to execute all orders")

    def _create_order(self, trade_instruction: SignalInstruction) -> BaseOrder:
        """
        Creates an order object based on the specified trade instruction.

        Args:
            trade_instruction (SignalInstruction): The trade instruction containing order details.

        Returns:
            BaseOrder: The created order object, ready for execution.

        Raises:
            RuntimeError: If the order creation fails due to invalid input parameters.
        """
        try:
            return trade_instruction.to_order()
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to create order due to input: {e}")

    def _set_order(
        self,
        timestamp: int,
        trade_id: int,
        leg_id: int,
        action: Action,
        contract: Contract,
        order: BaseOrder,
    ) -> None:
        """
        Queues an OrderEvent for execution based on the provided order details.

        Args:
            timestamp (int): The time at which the order was initiated (UNIX nanoseconds).
            trade_id (int): The unique trade identifier.
            leg_id (int): The identifier for the leg of a multi-leg trade.
            action (Action): The action for the trade (e.g., BUY, SELL, COVER).
            contract (Contract): The financial contract involved in the order.
            order (BaseOrder): The order object containing order specifications.

        Raises:
            RuntimeError: If creating the `OrderEvent` fails due to invalid input or unexpected errors.
        """
        try:
            order_event = OrderEvent(
                timestamp=timestamp,
                trade_id=trade_id,
                leg_id=leg_id,
                action=action,
                contract=contract,
                order=order,
            )
            self.notify(EventType.ORDER_CREATED, order_event)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to set OrderEvent due to input : {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error setting OrderEvent: {e}")

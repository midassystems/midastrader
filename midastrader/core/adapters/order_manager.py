import queue
import threading
from typing import List
from ibapi.contract import Contract

from midastrader.structs.symbol import SymbolMap
from midastrader.structs.events import SignalEvent, OrderEvent
from midastrader.message_bus import MessageBus, EventType
from midastrader.structs.signal import SignalInstruction
from midastrader.structs.orders import Action, BaseOrder
from midastrader.core.adapters.portfolio import PortfolioServer
from midastrader.core.adapters.order_book import OrderBook
from midastrader.core.adapters.base import CoreAdapter


class OrderExecutionManager(CoreAdapter):
    """
    Manages order execution based on trading signals.

    The `OrderExecutionManager` processes trading signals and initiates trade actions
    by interacting with the order book and portfolio server. It ensures that signals
    are validated against existing active orders and positions before executing any trades.
    """

    def __init__(self, symbols_map: SymbolMap, bus: MessageBus):
        """
        Initializes the OrderExecutionManager with required components.

        Args:
            symbols_map (SymbolMap): Mapping of symbol strings to `Symbol` objects.
            order_book (OrderBook): The order book reference for price lookups.
            portfolio_server (PortfolioServer): The portfolio server managing positions and account details.
        """
        super().__init__(symbols_map, bus)
        self.order_book = OrderBook.get_instance()
        self.portfolio_server = PortfolioServer.get_instance()
        self.running = threading.Event()

        # Subcriptions
        self.signal_queue = self.bus.subscribe(EventType.SIGNAL)

    def process(self) -> None:
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
        self.logger.info("Ordermanager running ...")
        self.running.set()

        while not self.shutdown_event.is_set():
            try:
                event = self.signal_queue.get()
                self.logger.info(f"Signal {event}")
                self.handle_event(event)
            except queue.Empty:
                continue

        self.cleanup()

    def cleanup(self):
        self.logger.info("Shutting down order execution manager...")

    def handle_event(self, event: SignalEvent) -> None:
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
            self.logger.debug("Ticker in signal has active order: ignoring.")
            self.bus.publish(EventType.UPDATE_SYSTEM, False)
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
            # self.logger.debug(trade)
            symbol = self.symbols_map.map[trade.instrument]
            order = trade.to_order()
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
            self.bus.publish(EventType.UPDATE_SYSTEM, False)

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
            self.bus.publish(EventType.ORDER, order_event)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to set OrderEvent due to input : {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error setting OrderEvent: {e}")

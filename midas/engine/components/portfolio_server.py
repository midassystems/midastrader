from typing import Dict
from midas.account import Account
from midas.positions import Position
from midas.engine.components.observer import Subject, Observer, EventType
from midas.active_orders import ActiveOrder
from midas.utils.logger import SystemLogger
from midas.symbol import SymbolMap


class OrderManager:
    """
    Manages the lifecycle and state of active orders in a trading system.

    The `OrderManager` class tracks active orders, processes updates to their status,
    and ensures positions are updated as needed. It integrates with a logging system
    for monitoring changes and provides utility methods to retrieve and display order information.

    Attributes:
        active_orders (Dict[int, ActiveOrder]): A dictionary of active orders keyed by their order ID.
        pending_positions_update (set): A set of tickers that require position updates.
        logger (SystemLogger): A logger instance for recording system events.
    """

    def __init__(self, logger: SystemLogger):
        self.active_orders: Dict[int, ActiveOrder] = {}
        self.pending_positions_update = set()
        self.logger = logger

    def get_active_order_tickers(self) -> list:
        """
        Retrieves a list of tickers that currently have active orders or pending position updates.

        Combines active order tickers with those requiring position updates, ensuring no duplicates.

        Returns:
            List[str]: List of tickers associated with active orders or pending updates.
        """
        active_order_tickers = [
            order.instrument for id, order in self.active_orders.items()
        ]

        # Combine with pending position updates and remove duplicates
        combined_tickers = list(
            set(active_order_tickers + list(self.pending_positions_update))
        )
        return combined_tickers

    def update_orders(self, order: ActiveOrder) -> None:
        """
        Updates the status of an order in the system.

        Handles additions, modifications, or removal of orders based on their status.
        Updates the `pending_positions_update` set when an order is filled.

        Args:
            order (ActiveOrder): The order to be updated.

        Behavior:
            - Removes orders with status "Cancelled" from active orders.
            - Removes filled orders and adds their tickers to `pending_positions_update`.
            - Updates or adds orders that are neither "Cancelled" nor "Filled".
        """
        # If the status is 'Cancelled' and the order is present in the dict, remove it
        if order.status == "Cancelled" and order.orderId in self.active_orders:
            del self.active_orders[order.orderId]
        elif order.status == "Filled" and order.orderId in self.active_orders:
            self.pending_positions_update.add(order.instrument)
            del self.active_orders[order.orderId]
        # If not cancelled, either update the existing order or add a new one
        elif order.status != "Cancelled" and order.status != "Filled":
            if order.orderId in self.active_orders:
                self.active_orders[order.orderId].update(order)
            else:
                self.active_orders[order.orderId] = order

        # self.notify(EventType.ORDER_UPDATE)  # update database
        self.logger.info(f"\nORDERS UPDATED: \n{self._ouput_orders()}")

    def _ouput_orders(self) -> str:
        """
        Generates a formatted string representation of all active orders for logging.

        Returns:
            str: String representation of active orders.
        """
        string = ""
        for permId, order in self.active_orders.items():
            string += f"{permId}:\n{order.pretty_print("  ")} \n"
        return string


class PositionManager:
    """
    Manages the positions held in a trading system.

    The `PositionManager` class is responsible for tracking and updating positions based on executed trades.
    It integrates with a logging system for monitoring changes and provides utility methods to retrieve
    and display position information.

    Attributes:
        positions (Dict[int, Position]): A dictionary of positions keyed by instrument ID.
        logger (SystemLogger): A logger instance for recording system events.
        pending_positions_update (set): A set of instrument IDs requiring position updates.
    """

    def __init__(self, logger: SystemLogger):
        """
        Initializes the PositionManager with a logging system.

        Args:
            logger (SystemLogger): Logger instance for recording events and updates.
        """
        self.positions: Dict[int, Position] = {}
        self.logger = logger
        self.pending_positions_update = set()

    @property
    def get_positions(self) -> Dict[int, Position]:
        """
        Retrieves the current positions.

        Returns:
            Dict[int, Position]: A dictionary of current positions keyed by instrument ID.
        """
        return self.positions

    def update_positions(self, instrument_id: int, position: Position) -> None:
        """
        Updates the position for a given instrument.

        Handles adding, updating, or removing positions based on the provided `position` data. If the
        position quantity is zero, the position is removed.

        Args:
            instrument_id (int): The unique identifier for the instrument.
            position (Position): The updated position data.

        Behavior:
            - Removes the position if the quantity is zero.
            - Updates the position if it exists or adds it if new.
            - Removes the instrument ID from `pending_positions_update`.
            - Logs the updated positions.
        """
        # Check if this position exists and is equal to the new position
        if position.quantity == 0:
            if instrument_id in self.positions:
                del self.positions[instrument_id]
            else:  # Same position duplicated, no need to log or notify
                return
        else:
            # Update the position
            self.positions[instrument_id] = position

        # Notify listener and log
        self.pending_positions_update.discard(instrument_id)
        self.logger.info(f"\nPOSITIONS UPDATED: \n{self._output_positions()}")

    def _output_positions(self) -> str:
        """
        Generates a formatted string representation of all positions for logging.

        Returns:
            str: A formatted string showing all positions with their details.
        """
        string = ""
        for id, position in self.positions.items():
            string += f"{id}:\n{position.pretty_print("  ")}\n"
        return string


class AccountManager:
    """
    Manages the account details in a trading system.

    The `AccountManager` class is responsible for maintaining and updating the account's details, such as capital.
    It integrates with a logging system to track changes and provides utility methods to retrieve account information.

    Attributes:
        account (Account): The account object containing details such as capital and other financial metrics.
        logger (SystemLogger): A logger instance for recording account updates.
    """

    def __init__(self, logger: SystemLogger):
        """
        Initializes the AccountManager with a logging system.

        Args:
            logger (SystemLogger): Logger instance for recording events and updates.
        """
        self.account: Account = None
        self.logger = logger

    @property
    def get_capital(self) -> float:
        """
        Retrieves the current available capital in the account.

        Returns:
            float: The current capital in the account.
        """
        return self.account.capital

    def update_account_details(self, account_details: Account) -> None:
        """
        Updates the account details in the system.

        This method replaces the current account object with the provided `account_details`
        and logs the updated information for tracking purposes.

        Notes:
            - The existing account details are completely replaced with the new data.
            - A log entry is created with the updated account information.

        Args:
            account_details (Account): The new account details, including capital
                and other metrics.

        """
        self.account = account_details
        self.logger.info(
            f"\nACCOUNT UPDATED: \n{self.account.pretty_print("  ")}"
        )


class PortfolioServer(Subject, Observer):
    """
    Manages and updates the state of the portfolio, including positions, orders, and account details.

    The `PortfolioServer` class acts as both a subject and an observer, handling updates to the portfolio
    and notifying observers of any changes. It integrates with position, order, and account managers to
    ensure accurate state management and provides utility methods for accessing portfolio details.

    Attributes:
        logger (SystemLogger): Logger instance for recording system events.
        order_manager (OrderManager): Manages the state and updates of orders.
        position_manager (PositionManager): Tracks and updates portfolio positions.
        account_manager (AccountManager): Manages account details such as capital and account metrics.
        symbols_map (SymbolMap): A mapping of symbol strings to `Symbol` objects for portfolio instruments.
    """

    def __init__(self, symbols_map: SymbolMap):
        """
        Initializes a new instance of the PortfolioServer.

        Parameters:
            symbols_map (SymbolMap): Mapping of symbol strings to `Symbol` objects for instruments.
        """
        Subject().__init__()
        self.logger = SystemLogger.get_logger()
        self.order_manager = OrderManager(self.logger)
        self.position_manager = PositionManager(self.logger)
        self.account_manager = AccountManager(self.logger)
        self.symbols_map = symbols_map

    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        *args,
        **kwargs,
    ) -> None:
        """
        Handles events and updates the portfolio state accordingly.

        Parameters:
            subject (Subject): The source of the event.
            event_type (EventType): The type of event (e.g., POSITION_UPDATE, ACCOUNT_UPDATE, ORDER_UPDATE).
            *args: Positional arguments required for the specific event type.
            **kwargs: Additional keyword arguments for handling the event.

        Raises:
            ValueError: If required arguments for an event type are missing or the event type is unhandled.
        """
        if event_type == EventType.POSITION_UPDATE:
            if len(args) == 2:
                self.position_manager.update_positions(args[0], args[1])
            else:
                raise ValueError(
                    "Missing required arguments for POSITION_UPDATE"
                )
        elif event_type == EventType.ACCOUNT_UPDATE:
            if len(args) == 1:
                self.account_manager.update_account_details(args[0])
            else:
                raise ValueError("Missing account details for ACCOUNT_UPDATE")
        elif event_type == EventType.ORDER_UPDATE:
            if len(args) == 1:
                self.order_manager.update_orders(args[0])
            else:
                raise ValueError("Missing order data for ORDER_UPDATE")

        else:
            raise ValueError(f"Unhandled event type: {event_type}")

    @property
    def capital(self) -> float:
        """
        Retrieves the available capital from the account.

        Returns:
            float: The current available capital.
        """
        return self.account_manager.get_capital

    @property
    def get_positions(self) -> Dict[int, Position]:
        """
        Retrieves the current positions in the portfolio.

        Returns:
            Dict[int, Position]: A dictionary of current positions keyed by instrument ID.
        """
        return self.position_manager.get_positions

    @property
    def get_account(self) -> Account:
        """
        Retrieves the account details of the portfolio.

        Returns:
            Account: The current account object.
        """
        return self.account_manager.account

    @property
    def get_active_orders(self) -> Dict[int, ActiveOrder]:
        """
        Retrieves the active orders in the portfolio.

        Returns:
            Dict[int, ActiveOrder]: A dictionary of active orders keyed by order ID.
        """
        return self.order_manager.active_orders

    def get_active_order_tickers(self) -> list:
        """
        Retrieves a list of tickers that currently have active orders.

        Returns:
            List[str]: A list of tickers with active orders.
        """
        return self.order_manager.get_active_order_tickers()

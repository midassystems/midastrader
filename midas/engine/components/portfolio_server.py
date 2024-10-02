from typing import Dict
from midas.account import Account
from midas.positions import Position
from midas.engine.components.observer import Subject, Observer, EventType
from midas.active_orders import ActiveOrder
from midas.utils.logger import SystemLogger
from midas.symbol import SymbolMap


class OrderManager:
    def __init__(self, logger):
        self.active_orders: Dict[int, ActiveOrder] = {}
        self.pending_positions_update = set()
        self.logger = logger

    def get_active_order_tickers(self) -> list:
        """
        Retrieves a list of tickers that currently have active orders.

        Returns:
        - List[str]: List of tickers with active orders.
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
        Updates the status of an order in the portfolio.

        Parameters:
        - order (ActiveOrder): The order to be updated.
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
        Generates a string representation of all active orders for logging.

        Returns:
        - str: String representation of active orders.
        """
        string = ""
        for permId, order in self.active_orders.items():
            string += f"{permId}:\n{order.pretty_print("  ")} \n"
        return string


class PositionManager:
    def __init__(self, logger):
        self.positions: Dict[int, Position] = {}
        self.logger = logger
        self.pending_positions_update = set()

    @property
    def get_positions(self):
        return self.positions

    def update_positions(self, instrument_id: int, position: Position) -> None:
        """
        Updates the position for a given contract.

        Parameters:
        - contract (Contract): The contract associated with the position.
        - new_position (Position): The new position to be updated.
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
        Generates a string representation of all positions for logging.

        Returns:
        - str: String representation of positions.
        """
        string = ""
        for id, position in self.positions.items():
            string += f"{id}:\n{position.pretty_print("  ")}\n"
        return string


class AccountManager:
    def __init__(self, logger):
        self.account = None
        self.logger = logger

    @property
    def get_capital(self):
        return self.account.capital

    def update_account_details(self, account_details: Account) -> None:
        """
        Updates the account details in the portfolio.

        Parameters:
        - account_details (AccountDetails): The updated account details.
        """
        self.account = account_details
        self.logger.info(
            f"\nACCOUNT UPDATED: \n{self.account.pretty_print("  ")}"
        )


class PortfolioServer(Subject, Observer):
    """
    Manages and updates the state of the portfolio including positions, orders, and account details, notifying observers of changes.
    """

    def __init__(self, symbols_map: SymbolMap):
        """
        Initializes a new instance of the PortfolioServer.

        Parameters:
        - symbols_map (Dict[str, Symbol]): Mapping of symbol strings to Symbol objects.
        - logger (logging.Logger): Logger for logging messages.
        - database (DatabaseClient, optional): Client for database operations.
        """
        Subject().__init__()
        self.logger = SystemLogger.get_logger()
        self.order_manager = OrderManager(self.logger)
        self.position_manager = PositionManager(self.logger)
        self.account_manager = AccountManager(self.logger)
        self.symbols_map = symbols_map

    def handle_event(
        self, subject: Subject, event_type: EventType, *args, **kwargs
    ):
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
    def capital(self):
        return self.account_manager.get_capital

    @property
    def get_positions(self):
        """Returns the current positions in the portfolio."""
        return self.position_manager.get_positions

    @property
    def get_account(self):
        """Returns the account details of the portfolio."""
        return self.account_manager.account

    @property
    def get_active_orders(self):
        """Returns the active orders in the portfolio."""
        return self.order_manager.active_orders

    def get_active_order_tickers(self) -> list:
        """
        Retrieves a list of tickers that currently have active orders.

        Returns:
        - List[str]: List of tickers with active orders.
        """
        return self.order_manager.get_active_order_tickers()

from ibapi.contract import Contract
from typing import Dict, Union
from midas.symbol import Symbol
from midas.engine.components.order_book import OrderBook
from midas.engine.events import ExecutionEvent
from midas.trade import Trade
from midas.orders import Action, BaseOrder
from midas.account import Account, EquityDetails
from midas.positions import position_factory, Position
from midas.utils.logger import SystemLogger
from midas.engine.components.observer.base import Subject, Observer, EventType
from midas.symbol import SymbolMap


class DummyBroker(Subject, Observer):
    """
    Simulates a broker for trading operations in a backtest environment.

    This class manages order placement, position management, account updates,
    and trade execution simulation. It maintains positions, account data, and
    handles operations like marking-to-market, margin call checks, and position liquidation.

    Attributes:
    - event_queue (Queue): The queue for posting execution events and other notifications.
    - order_book (OrderBook): The order book for retrieving market data and managing orders.
    - logger (Logger): The logger for recording broker activities and errors.
    - symbols_map (Dict[str, Symbol]): A mapping of ticker symbols to instrument details.
    - positions (Dict[Contract, PositionDetails]): Current positions held by the broker.
    - last_trade (Dict[str, ExecutionDetails]): Details of the last executed trades.
    - account (AccountDetails): Details of the broker's account including available funds, P&L, etc.
    """

    def __init__(
        self,
        symbols_map: SymbolMap,
        order_book: OrderBook,
        capital: float,
    ):
        """
        Initializes the DummyBroker with necessary components and account details.

        Parameters:
        - symbols_map (Dict[str, Symbol]): A dictionary mapping ticker symbols to instrument details.
        - event_queue (Queue): The queue for posting execution events.
        - order_book (OrderBook): The order book for managing orders and retrieving market data.
        - capital (float): Initial capital available in the broker's account.
        - logger (Logger): The logger instance for recording broker activities.
        """
        super().__init__()
        self.logger = SystemLogger.get_logger()
        self.order_book = order_book
        self.symbols_map = symbols_map

        # Variables
        self.positions: Dict[Contract, Position] = {}
        self.unrealized_pnl: Dict[str, float] = {"account": 0}
        self.margin_required: Dict[str, float] = {"account": 0}
        self.liquidation_value: Dict[str, float] = {"account": 0}
        self.last_trades: Dict[str, Trade] = {}
        self.last_trade: Union[Trade, None] = None
        self.account = Account(
            timestamp=None,
            full_available_funds=capital,
            net_liquidation=capital,
            full_init_margin_req=0,
            unrealized_pnl=0,
        )

    def handle_event(
        self,
        subject: Subject,
        event_type: EventType,
        event,
    ) -> None:
        if event_type == EventType.EOD_EVENT:
            self.logger.info(event)
            self.mark_to_market()
            self.check_margin_call()
            self.notify(EventType.EOD_EVENT, event)

    def placeOrder(
        self,
        timestamp: int,
        trade_id: int,
        leg_id: int,
        action: Action,
        contract: Contract,
        order: BaseOrder,
    ) -> None:
        """
        Simulates the placing fo an order to the broker in the backtest environment.

        Parameters:
        - timestamp (int): The timestamp of the order.
        - trade_id (int): The unique identifier for the trade.
        - leg_id (int): The identifier for the leg of the trade.
        - action (Action): The action to perform (BUY or SELL).
        - contract (Contract): The contract for which the order is placed.
        - order (BaseOrder): The order details including quantity, price, etc.
        """
        symbol = self.symbols_map.get_symbol(contract.symbol)

        # Order Data
        quantity = order.quantity  # +/- values
        mkt_data = self.order_book.retrieve(symbol.instrument_id)
        fill_price = symbol.slippage_price(mkt_data.pretty_price, action)
        fees = symbol.commission_fees(quantity)

        # Adjust cash by fees
        self.account.full_available_funds += fees

        # Update Positions
        self._update_positions(symbol, action, quantity, fill_price)

        # Update Account
        self._update_account()

        # Create Execution Events
        trade_details = self._update_trades(
            timestamp,
            trade_id,
            leg_id,
            symbol,
            quantity,
            action,
            fill_price,
            fees,
        )
        self._set_execution(timestamp, trade_details, action, symbol)

    def _update_positions(
        self,
        symbol: Symbol,
        action: Action,
        quantity: float,
        fill_price: float,
    ) -> None:
        """
        Updates the positions dictionary with the latest position details.

        Parameterss:
        - symbol (Symbol): The symbol object associated with the position update.
        - action (Action): The action associated with the position update (BUY, SELL, etc.).
        - quantity (float): The quantity of the order.
        - fill_price (float): The fill price of the order.

        Notes:
        - This method handles updating the broker's positions, including adding new positions, updating existing positions, and removing positions if they are closed out completely.
        """
        if symbol.contract not in self.positions:
            details = {
                "action": action.to_broker_standard(),
                "quantity": quantity,
                "avg_price": fill_price,
                "market_price": fill_price,
            }
            self.positions[symbol.contract] = position_factory(
                asset_type=symbol.security_type, symbol=symbol, **details
            )
            impact = self.positions[symbol.contract].position_impact()
        else:
            impact = self.positions[symbol.contract].update(
                quantity, fill_price, fill_price, action
            )

        # Update cash impact of position trade
        self.account.full_available_funds += impact.cash

    def _update_account(self):
        for contract, position in self.positions.items():
            symbol = self.symbols_map.get_symbol(contract.symbol)
            mkt_data = self.order_book.retrieve(symbol.instrument_id)
            position.market_price = mkt_data.pretty_price
            impact = position.position_impact()

            # Update postion specific account values
            self.unrealized_pnl[contract] = impact.unrealized_pnl
            self.margin_required[contract] = impact.margin_required
            self.liquidation_value[contract] = impact.liquidation_value

        # Update Account values
        self.account.unrealized_pnl = sum(
            value for key, value in self.unrealized_pnl.items()
        )
        self.account.full_init_margin_req = sum(
            value for key, value in self.margin_required.items()
        )
        self.account.net_liquidation = (
            sum(value for key, value in self.liquidation_value.items())
            + self.account.full_available_funds
        )
        self.account.timestamp = self.order_book.last_updated

    def _update_trades(
        self,
        timestamp: int,
        trade_id: int,
        leg_id: int,
        symbol: Symbol,
        quantity: float,
        action: Action,
        fill_price: float,
        fees: float,
    ) -> Trade:
        """
        Updates the broker's executed trades dictionary with details of the latest trade.

        Parameters:
        - timestamp (Union[int, float]): The timestamp of the trade.
        - trade_id (int): The ID of the trade.
        - leg_id (int): The ID of the leg of the trade.
        - contract (Contract): The contract associated with the trade.
        - quantity (float): The quantity of the trade.
        - action (Action): The action associated with the trade (BUY, SELL, etc.).
        - fill_price (float): The fill price of the trade.
        - fees (float): The commission fees incurred by the trade.

        Returns:
        - ExecutionDetails: Details of the executed trade.

        Notes:
        - This method updates the broker's executed trades dictionary with details of the latest trade for record-keeping.
        """
        trade = Trade(
            timestamp=timestamp,
            trade_id=trade_id,
            leg_id=leg_id,
            instrument=symbol.instrument_id,
            quantity=round(quantity, 4),
            avg_price=fill_price,
            trade_value=round(symbol.value(quantity, fill_price), 2),
            trade_cost=round(symbol.cost(quantity, fill_price), 2),
            action=action.value,
            fees=round(fees, 4),
        )

        self.last_trades[symbol.contract] = trade

        return trade

    def _set_execution(
        self,
        timestamp: int,
        trade_details: Trade,
        action: Action,
        symbol: Symbol,
    ) -> None:
        """
        Create and queue an ExecutionEvent based on trade details.

        Parameters:
        - timestamp (int): The timestamp of the execution.
        - trade_details (ExecutionDetails): Details of the executed trade.
        - action (Action): The action associated with the trade (BUY, SELL, etc.).
        - contract (Contract): The contract associated with the trade.
        """
        try:
            self.last_trade = trade_details
            execution_event = ExecutionEvent(
                timestamp, trade_details, action, symbol.contract
            )
            self.notify(EventType.TRADE_EXECUTED, execution_event)
        except (ValueError, TypeError) as e:
            raise RuntimeError(
                f"Failed to create or queue ExecutionEvent due to input error: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error when creating or queuing ExecutionEvent: {e}"
            ) from e

    def mark_to_market(self) -> None:
        """
        Marks all positions to market based on current market prices and updates account PnL accordingly.
        """
        self._update_account()
        self.logger.info("Account marked-to-market.")

    def check_margin_call(self) -> None:
        """
        Checks if a margin call is triggered based on available funds and initial margin requirements.

        Returns:
        - bool: True if a margin call is triggered, False otherwise.
        """
        # TODO: Logic to handle margin call, e.g., liquidate positions to meet margin requirements
        if self.account.check_margin_call():
            self.logger.info("Margin call triggered.")

    def liquidate_positions(self) -> None:
        """
        Liquidates all positions to allow for full performance calculations.
        """
        for contract, position in list(self.positions.items()):
            symbol = self.symbols_map.get_symbol(contract.symbol)
            mkt_data = self.order_book.retrieve(symbol.instrument_id)
            current_price = mkt_data.pretty_price
            position.market_price = current_price
            position.calculate_liquidation_value()

            trade = Trade(
                timestamp=self.order_book.last_updated,
                trade_id=self.last_trades[contract].trade_id,
                leg_id=self.last_trades[contract].leg_id,
                instrument=symbol.instrument_id,
                quantity=round(position.quantity * -1, 4),
                avg_price=current_price,
                trade_value=round(
                    symbol.value(position.quantity, current_price), 2
                ),
                trade_cost=symbol.cost(position.quantity * -1, current_price),
                action=(
                    Action.SELL.value
                    if position.action == "BUY"
                    else Action.COVER.value
                ),
                fees=0.0,  # because not actually a trade
            )

            self.last_trades[contract] = trade

        # Output liquidation
        string = "Positions liquidate:"
        for contract, trade in self.last_trades.items():
            string += f"\n  {contract} : {trade}"

        self.logger.info(f"\n{string}")

    def return_positions(self) -> dict:
        """
        Returns the current positions held by the broker.

        Returns:
        - dict: Dictionary containing current positions.
        """
        # Create a copy to return the original positions
        positions = self.positions.copy()

        # Keys to remove positions that are full-exited
        keys_to_remove = [
            contract
            for contract, position in self.positions.items()
            if position.quantity == 0
        ]
        for contract in keys_to_remove:
            del self.positions[contract]

        # Return positions includign exited positions
        return positions

    def return_account(self) -> dict:
        """
        Returns details of the broker's account.

        Returns:
        - dict: Dictionary containing account details.
        """
        return self.account

    def return_executed_trades(
        self, contract: Contract = None
    ) -> Union[dict, Trade]:
        """
        Returns details of executed trades.

        Parameters:
        - contract (Contract, optional): The contract associated with the executed trade. If provided, returns trade details for that contract only.

        Returns:
        - Union[dict, ExecutionDetails]: Dictionary or ExecutionDetails object containing details of executed trades.
        """
        if contract:
            return self.last_trades[contract]
        else:
            return self.last_trades

    def return_equity_value(self) -> EquityDetails:
        """
        Returns details of the broker's equity value.

        Returns:
        - EquityDetails: Details of the broker's equity value.
        """
        return self.account.equity_value()

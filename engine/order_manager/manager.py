import logging
from queue import Queue
from ibapi.order import Order
from ibapi.contract import Contract
from typing import Dict,List, Union

from engine.order_book import OrderBook
from engine.portfolio import PortfolioServer
from engine.events import  SignalEvent, OrderEvent

from shared.signal import TradeInstruction
from shared.symbol import Symbol, Future, Equity
from shared.orders import LimitOrder, MarketOrder, StopLoss, Action, OrderType, BaseOrder

class OrderManager:
    """
    Manages order execution based on trading signals, interfacing with a portfolio server and order book.
    """
    def __init__(self, symbols_map: Dict[str, Symbol], event_queue: Queue, order_book: OrderBook, portfolio_server: PortfolioServer, logger: logging.Logger):
        """
        Initialize the OrderManager with necessary components for managing orders.
        
        Parameters:
        - symbols_map (Dict[str, Symbol]): Mapping of symbol strings to Symbol objects.
        - event_queue (Queue): Event queue for sending events to other parts of the system.
        - order_book (OrderBook): Reference to the order book for price lookups.
        - portfolio_server (PortfolioServer): Reference to the portfolio server for managing account and positions.
        - logger (logging.Logger): Logger for logging messages.
        """
        self._event_queue = event_queue 
        self.portfolio_server = portfolio_server
        self.order_book = order_book
        self.logger = logger 

        self.symbols_map = symbols_map

    def on_signal(self, event: SignalEvent):
        """
        Handle received signal events by initiating trade actions if applicable.
        
        Parameters:
        - event (SignalEvent): The signal event containing trade instructions.
        """
        if not isinstance(event, SignalEvent):
            raise TypeError("'event' must be of type SignalEvent instance.")
        
        trade_capital = event.trade_capital
        trade_instructions = event.trade_instructions
        timestamp = event.timestamp

        # Assuming get_active_order_tickers() gives us a list of tickers in active orders
        active_orders_tickers = self.portfolio_server.get_active_order_tickers()
        self.logger.info(f"Active order tickers {active_orders_tickers}")
        
        # Check if any of the tickers in trade_instructions are in active orders or positions
        if any(trade.ticker in active_orders_tickers for trade in trade_instructions):
            self.logger.info("One or more tickers in the trade instructions have active orders; ignoring signal.")
            return
        else:
            self._handle_signal(timestamp,trade_capital, trade_instructions)

    def _handle_signal(self, timestamp: int, trade_capital: Union[int,float], trade_instructions: List[TradeInstruction])  -> None:
        """
        Process trade instructions to generate orders, checking if sufficient capital is available.

        Parameters:
        - timestamp (int): The time at which the signal was generated.
        - trade_capital (Union[int, float]): The amount of capital allocated for trading.
        - trade_instructions (List[TradeInstruction]): List of trading instructions to be processed.
        """
        # Create and Validate Orders
        orders = []
        total_capital_required = 0

        for trade in trade_instructions:
            trade
            order = self._order_details(trade, trade_capital)

            if isinstance(self.symbols_map[trade.ticker], Future):
                order_value = self._future_order_value(order.quantity, trade.ticker)
            elif isinstance(self.symbols_map[trade.ticker], Equity):
                order_value = self._equity_order_value(order.quantity, trade.ticker)
            else:
                raise ValueError(f"Symbol not of valid type : {self.symbols_map[trade.ticker]}")
            
            order_details = {
                'timestamp':timestamp,
                'trade_id':trade.trade_id,
                'leg_id':trade.leg_id,
                'action' : trade.action, 
                'contract': self.symbols_map[trade.ticker].contract, 
                'order' : order
            }
            
            orders.append(order_details)
            total_capital_required += order_value

        if (total_capital_required + self.portfolio_server.account['FullInitMarginReq']) <= self.portfolio_server.account['FullAvailableFunds']:
            for order in orders:
                self._set_order(order['timestamp'], order['trade_id'], order['leg_id'], order['action'], order['contract'],order['order'])
        else:
            self.logger.info("Not enough capital to execute all orders")

    def _future_order_value(self, quantity: float, ticker: str) -> float:
        """
        Calculate the required margin for a future order based on quantity.

        Parameters:
        - quantity (float): The quantity of the future order.
        - ticker (str): The ticker symbol for the future.

        Returns:
        - float: The calculated margin requirement for the future order.
        """
        return abs(quantity) * self.symbols_map[ticker].initialMargin
    
    def _equity_order_value(self, quantity: float, ticker: str) -> float:
        """
        Calculate the total value of an equity order based on quantity and current market price.

        Parameters:
        - quantity (float): The quantity of the equity order.
        - ticker (str): The ticker symbol for the equity.

        Returns:
        - float: The total value of the equity order.
        """
        return abs(quantity) * self.order_book.current_price(ticker)

    def _order_details(self, trade_instruction: TradeInstruction, position_allocation: float) -> BaseOrder:
        """
        Generate order details based on trade instructions and capital allocation.

        Parameters:
        - trade_instruction (TradeInstruction): The specific trade instruction.
        - position_allocation (float): The capital allocated to this particular trade.

        Returns:
        - BaseOrder: The generated order object.
        """
        ticker = trade_instruction.ticker
        action = trade_instruction.action
        weight = trade_instruction.weight
        current_price = self.order_book.current_price(ticker=ticker)
        
        # Retrieve multipliers
        price_multiplier = self.symbols_map[ticker].price_multiplier
        quantity_multiplier = self.symbols_map[ticker].quantity_multiplier

        # Order Capital
        order_allocation = position_allocation * abs(weight) 
        self.logger.info(f"\nOrder Allocation: {order_allocation}")

        # Order Quantity
        quantity = self._order_quantity(action,ticker,order_allocation,current_price,price_multiplier, quantity_multiplier)

        return self._create_order(trade_instruction.order_type,action,quantity)
    
    def _order_quantity(self, action: Action,ticker: str, order_allocation: float, current_price: float, price_multiplier: float , quantity_multiplier: int) -> float:
        """
        Calculate the order quantity based on allocation, price, and multipliers.

        Parameters:
        - action (Action): The trading action (LONG, SHORT, SELL, COVER).
        - ticker (str): The ticker symbol for the order.
        - order_allocation (float): The capital allocated for this order.
        - current_price (float): The current price of the ticker.
        - price_multiplier (float): The price adjustment factor for the ticker.
        - quantity_multiplier (int): The quantity adjustment factor for the ticker.

        Returns:
        - float: The calculated quantity for the order.
        """
        # Adjust current price based on the price multiplier
        adjusted_price = current_price * price_multiplier

        # Adjust quantity based on the trade allocation
        if action in [Action.LONG, Action.SHORT]:  # Entry signal
            quantity = order_allocation / (adjusted_price * quantity_multiplier) 
            # quantity *= 1 if action == Action.LONG else -1
        elif action in [Action.SELL, Action.COVER]:  # Exit signal
            quantity = self.portfolio_server.positions[ticker].quantity
            # quantity *= 1 if action == Action.COVER else -1
        return quantity
    
    def _create_order(self, order_type: OrderType, action : Action, quantity: float, limit_price: float=None, aux_price: float=None) -> float:
        """
        Create an order object based on specified parameters.

        Parameters:
        - order_type (OrderType): The type of order to create (MARKET, LIMIT, STOPLOSS).
        - action (Action): The action to be taken (BUY, SELL, etc.).
        - quantity (float): The quantity of the order.
        - limit_price (float, optional): The limit price for limit orders.
        - aux_price (float, optional): The auxiliary price for stop-loss orders.

        Returns:
        - BaseOrder: The created order object, ready for execution.
        """
        try:
            if order_type == OrderType.MARKET:
                return MarketOrder(action=action, quantity=quantity)
            elif order_type == OrderType.LIMIT:    
                return LimitOrder(action=action, quantity=quantity, limit_price=limit_price)
            elif order_type == OrderType.STOPLOSS:
                return StopLoss(action=action, quantity=quantity,aux_price=aux_price)
            else:
                raise ValueError(f"OrderType not of valid type : {order_type}")
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to create or queue SignalEvent due to input error: {e}") from e
    
    def _set_order(self, timestamp: int, trade_id: int, leg_id: int, action: Action, contract: Contract, order: BaseOrder) -> None:
        """
        Queue an OrderEvent based on the order details.

        Parameters:
        - timestamp (int): The timestamp when the order was initiated.
        - trade_id (int): The trade identifier.
        - leg_id (int): The leg identifier of the trade.
        - action (Action): The action of the trade (BUY, SELL, etc.).
        - contract (Contract): The contract involved in the order.
        - order (BaseOrder): The order to be executed.
        """
        try:
            order_event = OrderEvent(timestamp=timestamp, trade_id=trade_id, leg_id=leg_id, action=action, contract=contract, order=order)
            self._event_queue.put(order_event)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to create or queue OrderEvent due to input error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error when creating or queuing OrderEvent: {e}") from e

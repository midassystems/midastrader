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
    def __init__(self, symbols_map: Dict[str, Symbol], event_queue: Queue, order_book:OrderBook, portfolio_server: PortfolioServer, logger:logging.Logger):
        """
        Initialize the strategy with necessary parameters and components.

        Parameters:
            symbols_map (Dict[str, Contract]): Mapping of symbol strings to Contract objects.
            event_queue (Queue): Event queue for sending events to other parts of the system.
        """
        self._event_queue = event_queue 
        self.portfolio_server = portfolio_server
        self.order_book = order_book
        self.logger = logger 

        self.symbols_map = symbols_map

    def on_signal(self, event: SignalEvent):
        """ 
        Signal listener.
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

    def _handle_signal(self, timestamp:int, trade_capital: Union[int,float], trade_instructions:List[TradeInstruction]):
        """
        Converts trade instructions into OrderEvents based on capital and positions.

        Parameters:
            trade_instructions: List of trade instructions.
            market_data: Market data for the trades.
            current_capital: Current available capital.
            positions: Current open positions.

        Returns:
            List[OrderEvent]: The corresponding order events if there is enough capital, otherwise an empty list.
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

    def _future_order_value(self, quantity:float, ticker:str):
        return abs(quantity) * self.symbols_map[ticker].initialMargin
    
    def _equity_order_value(self, quantity:float, ticker:str):
        return abs(quantity) * self.order_book.current_price(ticker)

    def _order_details(self, trade_instruction:TradeInstruction, position_allocation:float):
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
    
    def _order_quantity(self, action:Action,ticker:str, order_allocation:float, current_price:float, price_multiplier: float , quantity_multiplier: int):
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
    
    def _create_order(self, order_type: OrderType, action : Action, quantity: float, limit_price: float=None, aux_price:float=None):
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
    
    def _set_order(self, timestamp:int, trade_id:int, leg_id:int, action: Action, contract: Contract, order: BaseOrder):
        """
        Create and queue an OrderEvent.

        Parameters:
            order_detail: Details of the order to be created and queued.
        """
        try:
            order_event = OrderEvent(timestamp=timestamp, trade_id=trade_id, leg_id=leg_id, action=action, contract=contract, order=order)
            self._event_queue.put(order_event)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to create or queue OrderEvent due to input error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error when creating or queuing OrderEvent: {e}") from e

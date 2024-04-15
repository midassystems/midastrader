import logging
from queue import Queue
from ibapi.order import Order
from ibapi.contract import Contract

from .dummy_broker import DummyBroker
from engine.portfolio import PortfolioServer
from engine.account_data import Position, Trade
from engine.performance import BasePerformanceManager
from engine.events import ExecutionEvent, Action, BaseOrder
from engine.events import ExecutionEvent, OrderEvent, TradeInstruction, Action

class BrokerClient:
    """
    Simulates the broker, controls the execution of trades and the updating of 'account' data.
    """
    def __init__(self,event_queue: Queue, logger: logging.Logger, portfolio_server: PortfolioServer, performance_manager: BasePerformanceManager, broker:DummyBroker):
        # Subscriptions
        self.performance_manager = performance_manager
        self.portfolio_server = portfolio_server
        self.broker = broker
        self.logger = logger
        self.event_queue = event_queue

        self.update_account()
        
    def on_order(self, event: OrderEvent):
        """
        The Order Event listener, called when a new order event is intercepted in the queue.

        Args:
            OrderEvent (Object) : Event with all the data related to a specific order to be executed.

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

    def handle_order(self, timestamp: int, trade_id: int, leg_id: int, action:Action, contract:Contract, order:BaseOrder):
        """
        Handles the the execution of the order, simulation the placing of order and creation of execution event.
        
        Args:
            contract (Object) : Class containing the specfics related to the symbol ex. ticker, exchange, currency
            order (Object) : Class that contains all the data related to a specific orde. ex OrderType(market, limit), and assocated data ex. limit price
            signal (Object) : Inititial signal object, used to pass signal data to trade client for updating the portfolio related fields.
            market_data (Object) : Initial MarketDataEvent, used to pass data not included in the signal or order to the trade client for portfolio updating.

        """
        self.broker.placeOrder(timestamp, trade_id, leg_id, action ,contract, order)

    def on_execution(self, event: ExecutionEvent):
        if not isinstance(event,ExecutionEvent):
            raise ValueError("'event' must be of type ExecutionEvent instance.")
        
        contract = event.contract
        
        self.update_positions()
        self.update_account()
        self.update_equity_value()
        self.update_trades(contract)
  
    def eod_update(self):
        self.broker.mark_to_market()
        self.broker.check_margin_call()
        self.update_account()
        self.update_equity_value()
   
    def update_positions(self):
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

    def update_trades(self, contract:Contract = None):
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
        account = self.broker.return_account()
        self.portfolio_server.update_account_details(account)

    def update_equity_value(self):
        self.broker._update_account_equity_value() 
        equity = self.broker.return_equity_value()
        self.performance_manager.update_equity(equity)
       
    def liquidate_positions(self):
        """
        Handles the liquidation of positions, typically on the last marketdataevent, to get allow for full performance calculations.
        """
        self.update_positions()
        self.update_account()
        self.update_equity_value()
        self.broker.liquidate_positions()
        self.update_trades()
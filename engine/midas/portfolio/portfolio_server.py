import logging
from typing import Dict
from ibapi.contract import Contract

from midas.symbols.symbols import Symbol
from midas.account_data import Position,ActiveOrder, AccountDetails
from client import DatabaseClient
from midas.observer import Subject, EventType

class PortfolioServer(Subject):
    """
    Interacts with the portfolio client, retrieves commonly needed data, that would be stored in the portfolio client.
    """
    def __init__(self, symbols_map: Dict[str, Symbol], logger:logging.Logger, database : DatabaseClient = None):
        """
        Class constructor.

        Args:
            portfolio_client (PortfolioClient) : Inherites the backtest portfolio client, so it can easily return portfoli related data to the engine.
        """
        super().__init__()
        self.symbols_map = symbols_map
        self.logger = logger
        self.database = database
  
        self.capital = None
        self.account : AccountDetails = {}
        self.positions : Dict[str, Position] = {}
        self.active_orders : Dict[int, ActiveOrder] = {}
        self.pending_positions_update = set()

    @property
    def get_positions(self):
        return self.positions
    
    @property
    def get_account(self):
        return self.account
    
    @property
    def get_active_orders(self):
        return self.active_orders
    
    def get_active_order_tickers(self) -> list:
        active_order_tickers = [order["symbol"] for id, order in self.active_orders.items()]
        # Combine with pending position updates and remove duplicates
        combined_tickers = list(set(active_order_tickers + list(self.pending_positions_update)))
        return combined_tickers
    
    def update_positions(self, contract: Contract, new_position: Position):
        # Check if this position exists and is equal to the new position
        if contract.symbol in self.positions and self.positions[contract.symbol] == new_position:
            return  # Positions are identical, do nothing
        else:
            # Update the position and log the change
            self.positions[contract.symbol] = new_position
            self.pending_positions_update.discard(contract.symbol)
            self.notify(EventType.POSITION_UPDATE)  # update database
            self.logger.info(f"\nPositions Updated: \n{self._output_positions()}")

    def _output_positions(self):
        string =""
        for contract, position in self.positions.items():
            string += f" {contract}: {position.__dict__} \n"
        return string
    
    def update_orders(self, order: ActiveOrder):
        # If the status is 'Cancelled' and the order is present in the dict, remove it
        if order['status'] == 'Cancelled' and order['orderId'] in self.active_orders:
            del self.active_orders[order['orderId']]
        elif order['status'] == 'Filled' and order['orderId'] in self.active_orders:
            self.pending_positions_update.add(order["symbol"])
            del self.active_orders[order['orderId']]
        # If not cancelled, either update the existing order or add a new one
        elif order['status'] != 'Cancelled' and order['status'] != 'Filled':
            if order['orderId'] not in self.active_orders:
                self.active_orders[order['orderId']] = order
            else:
                self.active_orders[order['orderId']].update(order)
        
        self.notify(EventType.ORDER_UPDATE)  # udpate dataabase
        self.logger.info(f"\nOrder Updated: \n{self._ouput_orders()}")

    def _ouput_orders(self):
        string =""
        for permId, order in self.active_orders.items():
            string += f" {order} \n"
        return string

    def update_account_details(self, account_details: AccountDetails):
        self.account = account_details
        self.capital = float(self.account['FullAvailableFunds'])
        self.notify(EventType.ACCOUNT_DETAIL_UPDATE)  
        self.logger.info(f"\nAccount Updated: \n{self._output_account()}")
    
    def _output_account(self):
        string = ""
        for key, value in self.account.items():
            string += f" {key} : {value} \n"
        return string
    



import logging
from queue import Queue
from ibapi.order import Order
from datetime import datetime
from ibapi.contract import Contract
from typing import Dict, Union, TypedDict, Union, Optional

from engine.order_book import OrderBook
from engine.symbols.symbols import Symbol, Future, Equity
from engine.account_data import AccountDetails,  EquityDetails
from engine.events import ExecutionEvent, Action, BaseOrder, TradeInstruction, ExecutionDetails

class PositionDetails(TypedDict):
    action: str
    avg_cost: float
    quantity: int
    price_multiplier: Optional[int]
    quantity_multiplier: Optional[int]
    initial_margin: Optional[float]
    unrealizedPnL :Optional[float]
    total_cost: Optional[float]

class DummyBroker:
    def __init__(self, symbols_map: Dict[str, Symbol], event_queue: Queue, order_book:OrderBook, capital:float, logger:logging.Logger,  slippage_factor:int=1):
        self.event_queue = event_queue
        self.order_book = order_book
        self.logger = logger
        self.symbols_map = symbols_map
        self.slippage_factor = slippage_factor # multiplied by tick size, so slippage will be x ticks against the position    
        
        # self.executions : Dict[str, ExecutionDetails] = {}
        self.positions : Dict[Contract, PositionDetails] = {}
        self.last_trade : Dict[str, ExecutionDetails] = {}
        self.account : AccountDetails =  {"Timestamp": None, 
                                          "FullAvailableFunds": capital,
                                          "NetLiquidation": capital, 
                                          "FullInitMarginReq": 0, 
                                          "UnrealizedPnL": 0
                                        }

    def placeOrder(self, timestamp: Union[int ,float], trade_id:int, leg_id:int, action: Action, contract: Contract, order: BaseOrder):
        # Order Data
        quantity = order.quantity # +/- values
        fill_price  = self._fill_price(contract, action)
        commission_fees = self._calculate_commission_fees(contract,quantity)
        
        # Update all account data(positions, account)
        self._update_account(contract, action, quantity, fill_price,commission_fees)

        # Create Execution Events
        trade_details = self._update_trades(timestamp, trade_id, leg_id, contract, quantity, action, fill_price, commission_fees)
        self._set_execution(timestamp, trade_details, action, contract)

    def _fill_price(self, contract: Contract, action:Action):
        """
        Accounts for slippage.
        """
        current_price = self.order_book.current_price(contract.symbol)

        if contract.secType == 'STK':
            tick_size = 1
        elif contract.secType == 'FUT':
            tick_size = self.symbols_map[contract.symbol].tickSize
        else:
            raise ValueError("'contract.sectype' must be one of the following : STK, FUT.")
        adjusted_price = self._slippage_adjust_price(tick_size, current_price, action)

        return adjusted_price

    def _slippage_adjust_price(self, tick_size: float, current_price: float, action: Action):
        slippage = tick_size * self.slippage_factor

        if action in [Action.LONG, Action.COVER]:  # Entry signal for a long position or covering a short
            adjusted_price = current_price + slippage
        elif action in [Action.SHORT, Action.SELL]:  # Entry signal for a short position or selling a long
            adjusted_price = current_price - slippage
        else:
            raise ValueError(f"'action' must be of type Action enum.")
        
        return adjusted_price

    def _calculate_commission_fees(self, contract: Contract, quantity: float):
        if contract.symbol in self.symbols_map:
            return abs(quantity) * self.symbols_map[contract.symbol].fees
        else:
            self.logger.error(f"Warning: Symbol {contract.symbol} not found in symbols map. Defaulting to 0 commission fees.")
            return 0
    
    def _update_account(self, contract: Contract, action: Action, quantity: float, fill_price: float, fees: float):
        if isinstance(self.symbols_map[contract.symbol], Future):
            self._update_account_futures(contract, action, quantity, fill_price, fees)
        elif isinstance(self.symbols_map[contract.symbol], Equity):
            self._update_account_equities(contract, action, quantity, fill_price, fees)
        else:
            raise ValueError(f"Symbol not of valid type : {self.symbols_map[contract.symbol]}")

        self._update_positions(contract, action, quantity, fill_price)
        self._update_account_equity_value()

    def _calculate_trade_pnl(self,position:PositionDetails, current_price:float, quantity:float):
        """
        Calculate the PnL.
        - If is_trade, quantity sign is adjusted to match the entry quantity for the trade.
        - If not a trade (position evaluation), use quantity as is.
        """
        quantity *= -1
        entry_value = position['avg_cost'] * quantity
        current_value = (current_price * position["price_multiplier"]) * (position['quantity_multiplier'] * quantity)
        pnl = current_value - entry_value
        return pnl
             
    def _pnl_per_contract(self, position:PositionDetails):
        return position['unrealizedPnL']/abs(position['quantity'])
    
    def _update_account_futures(self, contract: Contract, action: Action, quantity: float, fill_price: float, fees: float):
        self.account['FullAvailableFunds'] -= fees
        margin_impact = self.symbols_map[contract.symbol].initialMargin * abs(quantity)

        if action in [Action.LONG, Action.SHORT]: # Not a default clear position
            if contract not in self.positions.keys() or  self.positions[contract]['action'] == action: # eithernew postion or adding to old one
                self.account['FullInitMarginReq']  += margin_impact

            elif abs(self.positions[contract]['quantity']) > abs(quantity): # Reducing size of position
                pnl = self._calculate_trade_pnl(self.positions[contract],fill_price,quantity)
                realized_pnl = self._pnl_per_contract(self.positions[contract]) * quantity # pnl already marked to market
                self.account['FullAvailableFunds']  += pnl - realized_pnl # add just new pnl
                self.account['FullInitMarginReq'] -= self.symbols_map[contract.symbol].initialMargin * abs(quantity)  # remov margin for exited contracts
                self.positions[contract]['unrealizedPnL'] -= realized_pnl
            
            else: # flip a position
                pnl = self._calculate_trade_pnl(self.positions[contract],fill_price,quantity)
                self.account['FullAvailableFunds']  += pnl - self.positions[contract]['unrealizedPnL']
                self.account['FullInitMarginReq'] -= self.symbols_map[contract.symbol].initialMargin * abs(self.positions[contract]['quantity'])  
                self.account['FullInitMarginReq'] += self.symbols_map[contract.symbol].initialMargin * (abs(quantity) - abs(self.positions[contract]['quantity'])) 
                self.positions[contract]['unrealizedPnL'] = 0

        elif action in [Action.SELL, Action.COVER]: # complete exit of current position
            pnl = self._calculate_trade_pnl(self.positions[contract],fill_price,quantity)
            self.account['FullAvailableFunds']  += pnl - self.positions[contract]['unrealizedPnL']
            self.account['FullInitMarginReq'] -= self.symbols_map[contract.symbol].initialMargin * abs(quantity)  
       
    def _update_account_equities(self, contract: Contract, action: Action, quantity: float, fill_price: float, fees: float):
        self.account['FullAvailableFunds'] -= fees
        capital_impact = fill_price * abs(quantity) 

        if action in [Action.LONG, Action.COVER]:
            self.account['FullAvailableFunds']  -= capital_impact
        elif action in [Action.SELL, Action.SHORT]:         
            self.account['FullAvailableFunds']  += capital_impact
        else:
            raise ValueError("'action' must be of type Action enum.")
    
    def _update_positions(self, contract: Contract, action: Action, quantity: float, fill_price: float):
        ticker = contract.symbol
        price_multiplier = self.symbols_map[ticker].price_multiplier
        quantity_multiplier = self.symbols_map[ticker].quantity_multiplier
        action = action.to_broker_standard() # converts to BUY or SELL

        # If no position then postions is equal to new order attributes
        if contract not in self.positions.keys():
            self.positions[contract] = PositionDetails(
                action= action,
                quantity= quantity,
                avg_cost=round(((fill_price * price_multiplier) * quantity_multiplier),4),#TODO: valid this is how IB does it
                price_multiplier= price_multiplier,
                quantity_multiplier= quantity_multiplier,      
                initial_margin = self.symbols_map[ticker].initialMargin,
                unrealizedPnL=0
                # 'total_cost': round(quantity * avg_cost * -1,4) # Cost (-) if a buy, (+) if a sell    
            )
        else:
            current_position = self.positions[contract]
            existing_value = current_position['avg_cost'] * current_position['quantity']
            added_value = (fill_price * price_multiplier) * (quantity_multiplier * quantity)
            net_quantity = current_position['quantity'] + quantity

            # If nets the old position ot 0 the position no longer exists
            if net_quantity == 0:
                del self.positions[contract]

            # Adding to the old position
            elif action == current_position['action']:
                self.positions[contract]['quantity'] = net_quantity
                self.positions[contract]['avg_cost'] = (existing_value + added_value) / (net_quantity)
                # self.positions[contract]['total_cost'] = existing_value + added_value

            # If order less than current position quantity
            elif action != current_position['action'] and abs(quantity) < abs(current_position['quantity']):
                self.positions[contract]['quantity'] = net_quantity
                self.positions[contract]['total_cost'] = net_quantity * self.positions[contract]['avg_cost']
            
            # If order great than current position quantity
            elif action != current_position['action'] and abs(quantity) > abs(current_position['quantity']):
                # avg_cost = self.fill_price(contract,order.action)
                # quantity = self.check_action(order.action,order.totalquantity)
                self.positions[contract]['action'] = 'BUY' if net_quantity > 0 else 'SELL'
                self.positions[contract]['quantity'] = net_quantity
                self.positions[contract]['avg_cost'] = fill_price
                self.positions[contract]['total_cost'] = net_quantity * fill_price
            else: 
                raise ValueError(f"{action} not BUY or SELL")

    def _update_account_equity_value(self):
        portfolio_value = self._calculate_portfolio_value()
        
        current_equity_value = round(self.account['FullAvailableFunds'] +  portfolio_value, 2)
        self.account['NetLiquidation'] =  current_equity_value
        self.account['Timestamp'] = self.order_book.last_updated

    def _calculate_portfolio_value(self):
        portfolio_value = 0
        current_prices = self.order_book.current_prices()

        for contract, position in self.positions.items():
            current_price = current_prices[contract.symbol]
            if contract.secType == 'STK':
                portfolio_value += self._equity_position_value(position, current_price)
            elif contract.secType == 'FUT':
                portfolio_value += self._future_position_value(position, current_price)
            else:
                raise ValueError("'contract.sectype' must be one of the following : STK, FUT.")

        return portfolio_value
    
    def _future_position_value(self, position:PositionDetails, current_price:float):
        entry_cost = position['avg_cost'] * position['quantity'] 
        current_cost = (current_price * position['price_multiplier']) * (position['quantity_multiplier'] * position['quantity'])
        pnl = current_cost - entry_cost
        return pnl
    
    def _equity_position_value(self, position:PositionDetails, current_price:float):
        return (current_price * position['price_multiplier']) * (position['quantity_multiplier'] * position['quantity'])
    
    def _update_trades(self, timestamp: Union[int,float], trade_id:int, leg_id:int, contract:Contract, quantity: float, action: Action, fill_price:float, fees:float):
        quantity_multiplier = self.symbols_map[contract.symbol].quantity_multiplier
        price_multiplier = self.symbols_map[contract.symbol].price_multiplier

        trade = ExecutionDetails(
            timestamp = timestamp,
            trade_id = trade_id,
            leg_id = leg_id,
            symbol = contract.symbol,
            quantity = round(quantity,4),
            price = fill_price,
            cost = round((fill_price * price_multiplier) * (quantity * quantity_multiplier), 2),
            action = action.value,
            fees = round(fees,4)
        )

        self.last_trade[contract] = trade

        return trade
   
    def _set_execution(self, timestamp:int, trade_details: ExecutionDetails, action: Action, contract: Contract):
        """
        Create and queue an ExecutionEvent.

        Parameters:
            order_detail: Details of the order to be created and queued.
        """
        try:
            execution_event = ExecutionEvent(timestamp, trade_details, action, contract)
            self.event_queue.put(execution_event)
        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to create or queue ExecutionEvent due to input error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error when creating or queuing ExecutionEvent: {e}") from e
    
    def mark_to_market(self):
        total_new_pnl = 0
        self.account['UnrealizedPnL'] = 0
        current_prices = self.order_book.current_prices()

        for contract, position in self.positions.items():
            current_price = current_prices[contract.symbol]
            pnl = self._future_position_value(position, current_price) # total pnl for the position over life
            self.account['UnrealizedPnL'] += pnl  # current track of unrealized pnl for the account
            total_new_pnl += pnl - position['unrealizedPnL']  # new pnl on the postion since last updating
            position['unrealizedPnL'] = pnl # update postion pnl for new pnl

        self.account['FullAvailableFunds'] += total_new_pnl
        self.logger.info(f"Account marked-to-market.")

    def check_margin_call(self):
        if self.account['FullAvailableFunds']  < self.account['FullInitMarginReq']:
            self.logger.info("Margin call triggered.")
            # Logic to handle margin call, e.g., liquidate positions to meet margin requirements
            return True
        return False
    
    def liquidate_positions(self):
        """
        Handles the liquidation of positions, typically on the last marketdataevent, to get allow for full performance calculations.
        """
        for contract, position in list(self.positions.items()):
            action = Action.SELL if position['action'] == 'BUY' else Action.COVER
            fill_price = self._fill_price(contract,action)
            quantity = position['quantity'] * -1
            timestamp = self.order_book.book[contract.symbol].timestamp
            quantity_multiplier = self.symbols_map[contract.symbol].quantity_multiplier
            price_multiplier = self.symbols_map[contract.symbol].price_multiplier

            trade = ExecutionDetails(
                timestamp= timestamp,
                trade_id= self.last_trade[contract]['trade_id'],
                leg_id= self.last_trade[contract]['leg_id'],
                symbol= contract.symbol,
                quantity= round(quantity,4),
                price= fill_price,
                cost = round((fill_price * price_multiplier) * (quantity * quantity_multiplier), 2),
                action= action.value,
                fees= 0.0 # because not actually a trade
            )

            self.last_trade[contract] = trade

        self.logger.info(f"\nPositions liquidate: \n{self.last_trade}\n")
    
    # Return functions to mimic data return from broker
    def return_positions(self):
        return self.positions
    
    def return_account(self):
        return self.account
    
    def return_executed_trades(self, contract:Contract = None):
        if contract:
            return self.last_trade[contract]
        else:
            return self.last_trade

    def return_equity_value(self):
        return EquityDetails(
                timestamp= self.account['Timestamp'],
                equity_value = self.account['NetLiquidation']
                )
        
   
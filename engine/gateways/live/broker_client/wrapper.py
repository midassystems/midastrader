import os
import logging
import threading
from decimal import Decimal
from threading import Timer
from datetime import datetime
from ibapi.order import Order
from ibapi.client import EClient
from typing import get_type_hints
from ibapi.wrapper import EWrapper
from ibapi.execution import Execution
from ibapi.order_state import OrderState
from ibapi.contract import Contract, ContractDetails

from engine.portfolio import PortfolioServer
from engine.performance.live import LivePerformanceManager

from shared.portfolio import  Position,ActiveOrder, AccountDetails, EquityDetails

class BrokerApp(EWrapper, EClient):
    def __init__(self, logger:logging.Logger, portfolio_server: PortfolioServer, performance_manager: LivePerformanceManager):
        EClient.__init__(self, self)
        self.logger = logger
        self.portfolio_server = portfolio_server
        self.symbols_map = portfolio_server.symbols_map
        self.performance_manager = performance_manager

        #  Data Storage
        self.next_valid_order_id = None
        self.is_valid_contract = None
        self.account_info : AccountDetails = {} 
        self.account_info_keys = get_type_hints(AccountDetails)
        self.account_update_timer = None 
        self.account_update_lock = threading.Lock() 
        # self.executed_orders = {} 

        # Event Handling
        self.connected_event = threading.Event()
        self.valid_id_event = threading.Event()
        self.validate_contract_event = threading.Event()
        self.account_download_event = threading.Event()
        self.open_orders_event = threading.Event()

        # Thread Locks
        self.next_valid_order_id_lock = threading.Lock()

    def error(self, reqId:int, errorCode:int, errorString:str, advancedOrderRejectJson:str=None):
        super().error(reqId, errorCode, errorString)
        if errorCode == 502: # Error for wrong port
            self.logger.critical(f"Port Error : {errorCode} incorrect port entered.")
            os._exit(0)
        elif errorCode == 200: # Error for contract not found
            self.logger.critical(f"{errorCode} : {errorString}")
            self.is_valid_contract = False
            self.validate_contract_event.set()

    #### wrapper function to signifying completion of successful connection.      
    def connectAck(self):
        super().connectAck()
        self.logger.info('Established Broker Connection')
        self.connected_event.set()

    #### wrapper function for disconnect() -> Signals disconnection.
    def connectionClosed(self):
        super().connectionClosed()
        self.logger.info('Closed Broker Connection.')

    #### wrapper function for reqIds() -> This function manages the Order ID.
    def nextValidId(self, orderId:int):
        super().nextValidId(orderId)
        with self.next_valid_order_id_lock:
            self.next_valid_order_id = orderId
        
        self.logger.info(f"Next Valid Id {self.next_valid_order_id}")
        self.valid_id_event.set()

    def contractDetails(self, reqId:int, contractDetails: ContractDetails):
        self.is_valid_contract = True

    def contractDetailsEnd(self, reqId:int):
        self.logger.info(f"Contract Details Received.")
        self.validate_contract_event.set()
    
    #### wrapper function for reqAccountUpdates. returns accoutninformation whenever there is a change
    def updateAccountValue(self, key:str, val:str, currency:str, accountName:str):
        super().updateAccountValue(key, val, currency, accountName)

        if key in self.account_info_keys:
            if key == 'Currency':
                self.account_info[key] = val
            else:
                self.account_info[key] = float(val)
        
        if key == 'UnrealizedPnL':
            with self.account_update_lock:
                if self.account_update_timer is not None:
                    self.account_update_timer.cancel()
                self.account_update_timer = Timer(2, self.process_account_updates)  # 2 seconds delay
                self.account_update_timer.start()

    def process_account_updates(self):
        with self.account_update_lock:
            self.account_update_timer = None
            self.account_info['Timestamp'] = datetime.now().isoformat()
            # Copy the account_info to avoid modification during iteration
            account_info_copy = self.account_info.copy()
        
        # Updating portfolio server outside the lock to avoid deadlocks
        self.portfolio_server.update_account_details(account_info_copy)
        self.logger.info("Processed buffered account updates.")

    #### wrapper function for reqAccountUpdates. Get position information
    def updatePortfolio(self, contract:Contract, position: Decimal, marketPrice: float, marketValue:float, averageCost:float, unrealizedPNL:float, realizedPNL:float, accountName:str):
        super().updatePortfolio(contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName)
        if position == 0:
            pass
        else:
            position_data = Position(
                action="BUY" if position > 0 else "SELL",
                avg_cost = averageCost,
                quantity= float(position),
                total_cost= abs(float(position)) * averageCost if contract.secType =='FUT' else float(position) * averageCost,
                market_value=marketValue, 
                quantity_multiplier=self.symbols_map[contract.symbol].quantity_multiplier,
                price_multiplier=self.symbols_map[contract.symbol].price_multiplier,
                initial_margin=self.symbols_map[contract.symbol].initialMargin
            )
    
            self.portfolio_server.update_positions(contract, position_data)

    #### wrapper function for reqAccountUpdates. Signals the end of account information
    def accountDownloadEnd(self, accountName:str):
        super().accountDownloadEnd(accountName)

        # Cancel timer on intial download
        with self.account_update_lock:
            if self.account_update_timer is not None:
                self.account_update_timer.cancel()
                self.account_update_timer = None 

        self.process_account_updates()
        self.performance_manager.update_account_log(self.account_info.copy())

        self.logger.info(f"AccountDownloadEnd. Account: {accountName}")
        self.account_download_event.set()

    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState: OrderState):
        super().openOrder(orderId, contract, order, orderState)

        order_data = ActiveOrder(
            permId= order.permId,
            clientId= order.clientId, 
            orderId= orderId, 
            account= order.account, 
            symbol= contract.symbol, 
            secType= contract.secType,
            exchange= contract.exchange, 
            action= order.action, 
            orderType= order.orderType,
            totalQty= float(order.totalQuantity), # Decimal
            cashQty= order.cashQty, 
            lmtPrice= order.lmtPrice, 
            auxPrice= order.auxPrice, 
            status= orderState.status
        )
        self.portfolio_server.update_orders(order_data)

    # Wrapper function for openOrderEnd
    def openOrderEnd(self):
        self.logger.info(f"Initial Open Orders Received.")
        self.open_orders_event.set()

    # Wrapper function for orderStatus
    def orderStatus(self, orderId:int, status:str, filled:Decimal, remaining:Decimal, avgFillPrice:float, permId:int, parentId:int, lastFillPrice:float, clientId:int, whyHeld:str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        self.logger.info(f"Received order status update for orderId {orderId}: {status}")
        
        order_data = ActiveOrder(
            permId = permId,
            orderId =  orderId,
            status =  status, # Options : PendingSubmit, PendingCancel PreSubmitted, Submitted, Cancelled, Filled, Inactive 
            filled =  float(filled),
            remaining =  float(remaining),
            avgFillPrice =  avgFillPrice, 
            parentId =  parentId,
            lastFillPrice =  lastFillPrice, 
            whyHeld =  whyHeld, 
            mktCapPrice =  mktCapPrice
        )

        self.portfolio_server.update_orders(order_data)

    #### Wrapper function for reqAccountSummary
    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        super().accountSummary(reqId, account, tag, value, currency)

        if tag in self.account_info_keys:
            self.account_info[tag] = float(value)
        
        self.account_info["Currency"] = currency

    #### Wrapper function for end of reqAccountSummary
    def accountSummaryEnd(self, reqId: int):
        self.account_info['Timestamp'] = datetime.now().isoformat()
        self.logger.info(f"Account Summary Request Complete: {reqId}")

        self.performance_manager.update_account_log(self.account_info.copy())

    ####   wrapper function for reqExecutions.   this function gives the executed orders                
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        super().execDetails(reqId, contract, execution)
        side = "SELL" if execution.side == "SLD" else "BUY"

        execution_data = {
            "timestamp": execution.time, 
            "ticker": contract.symbol, 
            "quantity": format(execution.shares, 'f'),  # Decimal
            "cumQty": format(execution.cumQty, 'f'),  # Decimal
            "price": execution.price,
            "AvPrice": execution.avgPrice,
            "action": side,
            "cost":0,
            "currency": contract.currency, 
        }
        
        self.performance_manager.update_trades(execution.execId, execution_data)

    def commissionReport(self, commissionReport):
        self.performance_manager.update_trade_commission(commissionReport.execId, commissionReport.commission)


 
    
    
    
    

    
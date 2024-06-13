import os
import pytz
import time
import logging 
import threading
import numpy as np
from copy import deepcopy
from decimal import Decimal
from threading import Timer
from datetime import datetime
from ibapi.order import Order
from ibapi.client import EClient
from typing import get_type_hints
from ibapi.wrapper import EWrapper
from ibapi.execution import Execution
from ibapi.order_state import OrderState
from ibapi.commission_report import CommissionReport
from ibapi.contract import Contract, ContractDetails
from midas.engine.portfolio import PortfolioServer
from midas.shared.active_orders import ActiveOrder
from midas.shared.account import AccountDetails, Account
from midas.shared.positions import  Position, position_factory
# from midas.engine.performance.live import LivePerformanceManager

class BrokerApp(EWrapper, EClient):
    """
    Class representing the application interfacing with the broker's API.

    Attributes:
    - logger (logging.Logger): An instance of Logger for logging messages.
    - portfolio_server (PortfolioServer): An instance of PortfolioServer for managing portfolio data.
    - performance_manager (LivePerformanceManager): An instance of LivePerformanceManager for managing performance calculations.
    - symbols_map (dict): A dictionary mapping symbols to contract details.
    - next_valid_order_id (int): The next valid order ID.
    - is_valid_contract (bool): Flag indicating whether a contract is valid.
    - account_info (AccountDetails): Information about the account.
    - account_info_keys (dict_keys): Keys for account information.
    - account_update_timer (Timer): Timer for updating account information.
    - account_update_lock (threading.Lock): Lock for managing thread safety of account updates.
    - connected_event (threading.Event): Event signaling successful connection.
    - valid_id_event (threading.Event): Event signaling reception of valid order ID.
    - validate_contract_event (threading.Event): Event signaling successful contract validation.
    - account_download_event (threading.Event): Event signaling completion of account download.
    - open_orders_event (threading.Event): Event signaling reception of open orders.
    - next_valid_order_id_lock (threading.Lock): Lock for managing thread safety of order IDs.
    """
    def __init__(self, logger: logging.Logger, portfolio_server: PortfolioServer, performance_manager):
        """
        Initialize the BrokerApp instance.

        Parameters:
        - logger (logging.Logger): An instance of Logger for logging messages.
        - portfolio_server (PortfolioServer): An instance of PortfolioServer for managing portfolio data.
        - performance_manager (LivePerformanceManager): An instance of LivePerformanceManager for managing performance calculations.
        """
        EClient.__init__(self, self)
        self.logger = logger
        self.portfolio_server = portfolio_server
        self.symbols_map = portfolio_server.symbols_map
        self.performance_manager = performance_manager

        #  Data Storage
        self.next_valid_order_id = None
        self.is_valid_contract = None
        self.account_update_timer = None 
        self.account_info_keys = Account.get_account_key_mapping().keys()
        self.account_info = Account(
                                    timestamp=np.uint64(0),
                                    full_available_funds=0,
                                    full_init_margin_req=0,
                                    net_liquidation=0,
                                    unrealized_pnl=0
                                    )
        # self.executed_orders = {} 

        # Event Handling
        self.connected_event = threading.Event()
        self.valid_id_event = threading.Event()
        self.validate_contract_event = threading.Event()
        self.account_download_event = threading.Event()
        self.open_orders_event = threading.Event()

        # Thread Locks
        self.next_valid_order_id_lock = threading.Lock()
        self.account_update_lock = threading.Lock() 

    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str=None):
        """
        Handle errors from the broker's API.

        Parameters:
        - reqId (int): The request ID associated with the error.
        - errorCode (int): The error code.
        - errorString (str): The error message.
        - advancedOrderRejectJson (str, optional): JSON string containing advanced order rejection information. Defaults to None.
        """
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
        """Handle acknowledgment of successful connection."""
        super().connectAck()
        self.logger.info('Established Broker Connection')
        self.connected_event.set()

    #### wrapper function for disconnect() -> Signals disconnection.
    def connectionClosed(self):
        """Handle closure of the connection."""
        super().connectionClosed()
        self.logger.info('Closed Broker Connection.')

    #### wrapper function for reqIds() -> This function manages the Order ID.
    def nextValidId(self, orderId: int):
        """
        Handle receipt of the next valid order ID.

        Parameters:
        - orderId (int): The next valid order ID.
        """
        super().nextValidId(orderId)
        with self.next_valid_order_id_lock:
            self.next_valid_order_id = orderId
        
        self.logger.info(f"Next Valid Id {self.next_valid_order_id}")
        self.valid_id_event.set()

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        """
        Handle receipt of contract details.

        Parameters:
        - reqId (int): The request ID associated with the contract details.
        - contractDetails (ContractDetails): Details of the contract.
        """
        self.is_valid_contract = True

    def contractDetailsEnd(self, reqId: int):
        """
        Handle end of contract details.

        Parameters:
            reqId (int): The request ID associated with the end of contract details.
        """
        self.logger.info(f"Contract Details Received.")
        self.validate_contract_event.set()
    
    #### wrapper function for reqAccountUpdates. returns accoutninformation whenever there is a change
    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        """
        Handle updates to account values.

        Parameters:
        - key (str): The key of the account value.
        - val (str): The value of the account value.
        - currency (str): The currency of the account.
        - accountName (str): The name of the account.
        """
        super().updateAccountValue(key, val, currency, accountName)

        if key in self.account_info_keys:
            if key == 'Currency':
                self.account_info.update_from_broker_data(key, val)
            else:
                self.account_info.update_from_broker_data(key, float(val))
                # self.account_info[key] = float(val)
        
        if key == 'UnrealizedPnL':
            with self.account_update_lock:
                if self.account_update_timer is not None:
                    self.account_update_timer.cancel()
                self.account_update_timer = Timer(2, self.process_account_updates)  # 2 seconds delay
                self.account_update_timer.start()

    def process_account_updates(self):
        """Process buffered account updates."""
        with self.account_update_lock:
            self.account_update_timer = None
            self.account_info.timestamp = int(time.time() * 1e9)

            # Copy the account_info to avoid modification during iteration
            account_info_copy = deepcopy(self.account_info)
        
        # Updating portfolio server outside the lock to avoid deadlocks
        self.portfolio_server.update_account_details(account_info_copy)
        self.logger.info("Processed buffered account updates.")

    #### wrapper function for reqAccountUpdates. Get position information
    def updatePortfolio(self, contract: Contract, position: Decimal, marketPrice: float, marketValue: float, averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        """
        Handle updates to the portfolio.

        Parameters:
        - contract (Contract): The contract associated with the position.
        - position (Decimal): The position.
        - marketPrice (float): The market price.
        - marketValue (float): The market value.
        - averageCost (float): The average cost.
        - unrealizedPNL (float): The unrealized profit/loss.
        - realizedPNL (float): The realized profit/loss.
        - accountName (str): The name of the account.
        """
        super().updatePortfolio(contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName)
        symbol = self.symbols_map[contract.symbol]

        details = {
            "action": "BUY" if position > 0 else "SELL",
            "avg_price": averageCost,
            "quantity": float(position),
            "market_price": marketPrice,
            # "market_value":marketValue,
            # "unrealized_pnl":unrealizedPNL 
        }

        position = position_factory(symbol.security_type, symbol,**details)
        self.portfolio_server.update_positions(contract, position)

        
        # if position == 0:
        #     pass
        # else:
        #     position_data = Position(
        #         action="BUY" if position > 0 else "SELL",
        #         avg_cost = averageCost,
        #         quantity= float(position),
        #         total_cost= abs(float(position)) * averageCost if contract.secType =='FUT' else float(position) * averageCost,
        #         market_value=marketValue, 
        #         quantity_multiplier=self.symbols_map[contract.symbol].quantity_multiplier,
        #         price_multiplier=self.symbols_map[contract.symbol].price_multiplier,
        #         initial_margin=self.symbols_map[contract.symbol].initialMargin
        #     )
    

    #### wrapper function for reqAccountUpdates. Signals the end of account information
    def accountDownloadEnd(self, accountName: str):
        """
        Handle completion of account download.

        Parameters:
        - accountName (str): The name of the account.
        """
        super().accountDownloadEnd(accountName)

        # Cancel timer on intial download
        with self.account_update_lock:
            if self.account_update_timer is not None:
                self.account_update_timer.cancel()
                self.account_update_timer = None 

        self.process_account_updates()
        self.performance_manager.update_account_log(self.account_info.to_dict())

        self.logger.info(f"AccountDownloadEnd. Account: {accountName}")
        self.account_download_event.set()

    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState: OrderState):
        """
        Handle receipt of open orders.

        Parameters:
        - orderId (int): The order ID.
        - contract (Contract): The contract associated with the order.
        - order (Order): The order.
        - orderState (OrderState): The state of the order.
        """
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
        """Handle end of open orders."""
        self.logger.info(f"Initial Open Orders Received.")
        self.open_orders_event.set()

    # Wrapper function for orderStatus
    def orderStatus(self, orderId: int, status: str, filled: Decimal, remaining: Decimal, avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        """
        Handle order status updates.

        Parameters:
        - orderId (int): The order ID.
        - status (str): The status of the order.
        - filled (Decimal): The filled quantity.
        - remaining (Decimal): The remaining quantity.
        - avgFillPrice (float): The average fill price.
        - permId (int): The permanent order ID.
        - parentId (int): The parent order ID.
        - lastFillPrice (float): The price of the last fill.
        - clientId (int): The client ID.
        - whyHeld (str): Reason for order hold.
        - mktCapPrice (float): Market cap price.
        """
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
        """
        Method called upon receiving account summary.

        Parameters:
        - reqId (int): The request ID associated with the account summary.
        - account (str): The account.
        - tag (str): The tag.
        - value (str): The value.
        - currency (str): The currency of the account.
        """
        super().accountSummary(reqId, account, tag, value, currency)

        if tag in self.account_info_keys:
            self.account_info.update_from_broker_data(tag, float(value))
            # self.account_info[tag] = float(value)
            
        self.account_info.currency = currency

    #### Wrapper function for end of reqAccountSummary
    def accountSummaryEnd(self, reqId: int):
        """
        Method called upon the end of receiving account summary.

        Parameters:
        - reqId (int): The request ID associated with the account summary.
        """
        self.account_info.timestamp= int(time.time() * 1e9)
        self.logger.info(f"Account Summary Request Complete: {reqId}")

        self.performance_manager.update_account_log(self.account_info.to_dict())

    ####   wrapper function for reqExecutions.   this function gives the executed orders                
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        """
        Method called upon receiving execution details.

        Parameters:
        - reqId (int): The request ID associated with the execution details.
        - contract (Contract): The contract.
        - execution (Execution): The execution details.
        """
        super().execDetails(reqId, contract, execution)
        side = "SELL" if execution.side == "SLD" else "BUY"

        datetime_part, timezone_part = execution.time.rsplit(" ", 1)

        # Now use the split parts with the previously defined method
        unix_ns = datetime_to_unix_ns(datetime_part, timezone_part)

        execution_data = {
            "timestamp": unix_ns, 
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

    def commissionReport(self, commissionReport: CommissionReport):
        """
        Method called upon receiving commission report.

        Parameters:
        - commissionReport (CommissionReport): The commission report.
        """
        self.performance_manager.update_trade_commission(commissionReport.execId, commissionReport.commission)


def datetime_to_unix_ns(datetime_str: str, timezone_str: str):
    """
    Convert a datetime string with a specified timezone to Unix time in nanoseconds.

    Parameters:
    - datetime_str (str): The datetime string in the format "YYYYMMDD HH:MM:SS".
    - timezone_str (str): The timezone string, e.g., "US/Central".

    Returns:
    - int: Unix timestamp in nanoseconds.
    """
    # Parse the datetime part
    dt_naive = datetime.strptime(datetime_str, "%Y%m%d %H:%M:%S")

    # Attach the timezone to the datetime object using pytz
    timezone = pytz.timezone(timezone_str)
    dt_aware = timezone.localize(dt_naive)

    # Convert the timezone-aware datetime object to a Unix timestamp in seconds
    unix_timestamp_seconds = dt_aware.timestamp()

    # Convert the Unix timestamp to nanoseconds
    unix_timestamp_nanoseconds = int(unix_timestamp_seconds * 1e9)

    return unix_timestamp_nanoseconds
    
    

    
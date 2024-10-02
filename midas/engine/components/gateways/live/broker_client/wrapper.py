import os
import pytz
import time
import threading
from copy import deepcopy
from decimal import Decimal
from threading import Timer
from datetime import datetime
from ibapi.order import Order
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from midas.trade import Trade
from ibapi.execution import Execution
from ibapi.order_state import OrderState
from midas.account import Account
from midas.positions import position_factory
from midas.active_orders import ActiveOrder
from ibapi.commission_report import CommissionReport
from ibapi.contract import Contract, ContractDetails
from midas.utils.logger import SystemLogger
from midas.engine.components.observer.base import Subject, EventType
from midas.symbol import SymbolMap


class BrokerApp(EWrapper, EClient, Subject):
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

    def __init__(self, symbols_map: SymbolMap):
        """
        Initialize the BrokerApp instance.

        Parameters:
        - logger (logging.Logger): An instance of Logger for logging messages.
        - portfolio_server (PortfolioServer): An instance of PortfolioServer for managing portfolio data.
        - performance_manager (LivePerformanceManager): An instance of LivePerformanceManager for managing performance calculations.
        """
        EClient.__init__(self, self)
        Subject.__init__(self)
        self.logger = SystemLogger.get_logger()
        self.symbols_map = symbols_map

        #  Data Storage
        self.next_valid_order_id = None
        self.is_valid_contract = None
        self.account_update_timer = None
        self.account_info_keys = Account.get_account_key_mapping().keys()
        self.account_info = Account(
            timestamp=0,
            full_available_funds=0,
            full_init_margin_req=0,
            net_liquidation=0,
            unrealized_pnl=0,
        )
        self.last_order_id = 0

        # Event Handling
        self.connected_event = threading.Event()
        self.valid_id_event = threading.Event()
        self.validate_contract_event = threading.Event()
        self.account_download_event = threading.Event()
        self.open_orders_event = threading.Event()

        # Thread Locks
        self.next_valid_order_id_lock = threading.Lock()
        self.account_update_lock = threading.Lock()

    def error(
        self,
        reqId: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson: str = None,
    ):
        """
        Handle errors from the broker's API.

        Parameters:
        - reqId (int): The request ID associated with the error.
        - errorCode (int): The error code.
        - errorString (str): The error message.
        - advancedOrderRejectJson (str, optional): JSON string containing advanced order rejection information. Defaults to None.
        """
        super().error(reqId, errorCode, errorString)
        if errorCode == 502:  # Error for wrong port
            self.logger.critical(
                f"Port Error : {errorCode} incorrect port entered."
            )
            os._exit(0)
        elif errorCode == 200:  # Error for contract not found
            self.logger.critical(f"{errorCode} : {errorString}")
            self.is_valid_contract = False
            self.validate_contract_event.set()

    #### wrapper function to signifying completion of successful connection.
    def connectAck(self):
        """handle acknowledgment of successful connection."""
        super().connectAck()
        self.logger.info("Established Broker Connection")
        self.connected_event.set()

    #### wrapper function for disconnect() -> signals disconnection.
    def connectionClosed(self):
        """handle closure of the connection."""
        super().connectionClosed()
        self.logger.info("Closed Broker Connection.")

    #### wrapper function for reqids() -> this function manages the order id.
    def nextValidId(self, orderId: int):
        """
        handle receipt of the next valid order id.
        parameters:
        - orderid (int): the next valid order id.
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
        self.logger.info("Contract Details Received.")
        self.validate_contract_event.set()

    #### wrapper function for reqAccountUpdates. returns accoutninformation whenever there is a change
    def updateAccountValue(
        self, key: str, val: str, currency: str, accountName: str
    ):
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
            if key == "Currency":
                self.account_info.update_from_broker_data(key, val)
            else:
                self.account_info.update_from_broker_data(key, float(val))

        if key == "UnrealizedPnL":
            with self.account_update_lock:
                if self.account_update_timer is not None:
                    self.account_update_timer.cancel()
                # 2 seccond delay
                self.account_update_timer = Timer(
                    2,
                    self.process_account_updates,
                )
                self.account_update_timer.start()

    def process_account_updates(self):
        """Process buffered account updates."""
        with self.account_update_lock:
            self.account_update_timer = None
            self.account_info.timestamp = int(time.time() * 1e9)

            # Copy the account_info to avoid modification during iteration
            account_info_copy = deepcopy(self.account_info)

        # Updating portfolio server outside the lock to avoid deadlocks
        self.notify(EventType.ACCOUNT_UPDATE, account_info_copy)
        self.logger.info("Processed buffered account updates.")

    #### wrapper function for reqAccountUpdates. Get position information
    def updatePortfolio(
        self,
        contract: Contract,
        position: Decimal,
        marketPrice: float,
        marketValue: float,
        averageCost: float,
        unrealizedPNL: float,
        realizedPNL: float,
        accountName: str,
    ):
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
        super().updatePortfolio(
            contract,
            position,
            marketPrice,
            marketValue,
            averageCost,
            unrealizedPNL,
            realizedPNL,
            accountName,
        )

        if contract.symbol in self.symbols_map.broker_tickers:
            symbol = self.symbols_map.get_symbol(contract.symbol)
            market_price = marketPrice / symbol.price_multiplier
            avg_price = averageCost / (
                symbol.price_multiplier * symbol.quantity_multiplier
            )

            details = {
                "action": "BUY" if position > 0 else "SELL",
                "avg_price": avg_price,
                "quantity": float(position),
                "market_price": market_price,
            }

            position = position_factory(
                symbol.security_type, symbol, **details
            )
            self.notify(
                EventType.POSITION_UPDATE, symbol.instrument_id, position
            )

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
        self.notify(EventType.ACCOUNT_UPDATE, self.account_info)

        self.logger.info(f"AccountDownloadEnd. Account: {accountName}")
        self.account_download_event.set()

    def openOrder(
        self,
        orderId: int,
        contract: Contract,
        order: Order,
        orderState: OrderState,
    ):
        """
        Handle receipt of open orders.

        Parameters:
        - orderId (int): The order ID.
        - contract (Contract): The contract associated with the order.
        - order (Order): The order.
        - orderState (OrderState): The state of the order.
        """
        super().openOrder(orderId, contract, order, orderState)
        instrument = self.symbols_map.get_id(contract.symbol)

        if self.last_order_id < orderId:
            order_data = ActiveOrder(
                permId=order.permId,
                clientId=order.clientId,
                orderId=orderId,
                parentId=order.parentId,
                account=order.account,
                instrument=instrument,
                secType=contract.secType,
                exchange=contract.exchange,
                action=order.action,
                orderType=order.orderType,
                totalQty=float(order.totalQuantity),  # Decimal
                cashQty=order.cashQty,
                lmtPrice=order.lmtPrice,
                auxPrice=order.auxPrice,
                status=orderState.status,
            )
            self.logger.info(f"Received new order : {orderId}")

            # Update last new order id
            self.last_order_id = orderId

            # Update portfoli server orders log
            self.notify(EventType.ORDER_UPDATE, order_data)

    # Wrapper function for openOrderEnd
    def openOrderEnd(self):
        """Handle end of open orders."""
        self.logger.info("Initial Open Orders Received.")
        self.open_orders_event.set()

    # Wrapper function for orderStatus
    def orderStatus(
        self,
        orderId: int,
        status: str,
        filled: Decimal,
        remaining: Decimal,
        avgFillPrice: float,
        permId: int,
        parentId: int,
        lastFillPrice: float,
        clientId: int,
        whyHeld: str,
        mktCapPrice: float,
    ):
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
        super().orderStatus(
            orderId,
            status,
            filled,
            remaining,
            avgFillPrice,
            permId,
            parentId,
            lastFillPrice,
            clientId,
            whyHeld,
            mktCapPrice,
        )
        self.logger.info(f"Received order status update : {orderId}")

        order_data = ActiveOrder(
            permId=permId,
            orderId=orderId,
            clientId=clientId,
            parentId=parentId,
            status=status,
            filled=float(filled),
            remaining=float(remaining),
            avgFillPrice=avgFillPrice,
            lastFillPrice=lastFillPrice,
            whyHeld=whyHeld,
            mktCapPrice=mktCapPrice,
        )
        self.notify(EventType.ORDER_UPDATE, order_data)

    #### Wrapper function for reqAccountSummary
    def accountSummary(
        self, reqId: int, account: str, tag: str, value: str, currency: str
    ):
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

        self.account_info.currency = currency

    #### Wrapper function for end of reqAccountSummary
    def accountSummaryEnd(self, reqId: int):
        """
        Method called upon the end of receiving account summary.

        Parameters:
        - reqId (int): The request ID associated with the account summary.
        """
        self.account_info.timestamp = int(time.time() * 1e9)
        self.logger.info(f"Account Summary Request Complete: {reqId}")
        self.notify(EventType.ACCOUNT_UPDATE, self.account_info)

    ####   wrapper function for reqExecutions.   this function gives the executed orders
    def execDetails(
        self, reqId: int, contract: Contract, execution: Execution
    ):
        """
        Method called upon receiving execution details.

        Parameters:
        - reqId (int): The request ID associated with the execution details.
        - contract (Contract): The contract.
        - execution (Execution): The execution details.
        """
        self.logger.info(f"Recieved trade details : {execution.orderId}")
        super().execDetails(reqId, contract, execution)

        # Symbol
        if contract.symbol in self.symbols_map.broker_tickers:
            symbol = self.symbols_map.get_symbol(contract.symbol)

            # Convert action to ["BUY", "SELL"]
            side = "SELL" if execution.side == "SLD" else "BUY"

            # get timestamp in nanoseconds UNIX
            datetime_part, timezone_part = execution.time.rsplit(" ", 1)
            unix_ns = datetime_to_unix_ns(datetime_part, timezone_part)

            # Data
            quantity = float(execution.shares)
            price = execution.price

            # Create Trade
            trade = Trade(
                timestamp=unix_ns,
                instrument=symbol.instrument_id,
                trade_id=execution.orderId,
                leg_id=1,
                quantity=quantity,  # Decimal
                avg_price=price,
                trade_value=round(symbol.value(quantity, price), 2),
                trade_cost=round(symbol.cost(quantity, price), 2),
                action=side,
                fees=0,
            )
            self.notify(EventType.TRADE_UPDATE, execution.execId, trade)

    def commissionReport(self, commissionReport: CommissionReport):
        """
        Method called upon receiving commission report.

        Parameters:
        - commissionReport (CommissionReport): The commission report.
        """
        self.notify(
            EventType.TRADE_COMMISSION_UPDATE,
            commissionReport.execId,
            commissionReport.commission,
        )


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

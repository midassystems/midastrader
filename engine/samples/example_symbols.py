from core.base.data import Equity, Future, Currency, Exchange

gold_future = Future(symbol="GC",currency=Currency.USD, exchange=Exchange.COMEX,lastTradeDateOrContractMonth= "202312")
corn_future = Future(symbol="ZC", currency=Currency.USD, exchange=Exchange.CBOT, lastTradeDateOrContractMonth="202312")
SP_future = Future(symbol = "ES", currency=Currency.USD, exchange=Exchange.CME, lastTradeDateOrContractMonth="202312")
NASDAQ_future = Future(symbol = "NQ", currency=Currency.USD, exchange=Exchange.CME, lastTradeDateOrContractMonth="202312")
oil_future = Future(symbol = "CL", currency=Currency.USD, exchange=Exchange.NYMEX, lastTradeDateOrContractMonth="202312")
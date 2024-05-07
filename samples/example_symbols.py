from midas.shared.symbol import Equity, Future, Currency, Venue

gold_future = Future(symbol="GC",currency=Currency.USD, exchange=Venue.COMEX,lastTradeDateOrContractMonth= "202312")
corn_future = Future(symbol="ZC", currency=Currency.USD, exchange=Venue.CBOT, lastTradeDateOrContractMonth="202312")
SP_future = Future(symbol = "ES", currency=Currency.USD, exchange=Venue.CME, lastTradeDateOrContractMonth="202312")
NASDAQ_future = Future(symbol = "NQ", currency=Currency.USD, exchange=Venue.CME, lastTradeDateOrContractMonth="202312")
oil_future = Future(symbol = "CL", currency=Currency.USD, exchange=Venue.NYMEX, lastTradeDateOrContractMonth="202312")
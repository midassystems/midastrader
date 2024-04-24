import pandas as pd
from decouple import config
from datetime import datetime, timedelta
from ..client import DatabaseClient
from shared.symbol import SecurityType, Venue, Industry ,Currency, ContractUnits,AssetClass,  Equity, Future, Option, Index

pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000) # Adjust the width of the display in characters
pd.set_option('display.max_rows', None)

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

if __name__ == "__main__":
    # Initialize the database client
    database = DatabaseClient(DATABASE_KEY,DATABASE_URL) 
    
    try:
        index=Index(ticker="^GSPC",
                    security_type=SecurityType.INDEX,
                    name="S&P 500",
                    currency=Currency.USD,
                    asset_class=AssetClass.EQUITY)

        database.create_symbol(index)

        future= Future(ticker = "HE.n.0",
            data_ticker = "HE.n.0",
            currency = Currency.USD,  
            exchange = Venue.CME,  
            fees = 0.85,  
            initialMargin =4564.17,
            quantity_multiplier=40000,
            price_multiplier=0.01,
            product_code="HE",
            product_name="Lean Hogs",
            industry=Industry.AGRICULTURE,
            contract_size=40000,
            contract_units=ContractUnits.POUNDS,
            tick_size=0.00025,
            min_price_fluctuation=10,
            continuous=False,
            lastTradeDateOrContractMonth="202404")
        
        database.create_symbol(future)

        future=Future(ticker = "ZC.n.0",
                data_ticker = "ZC.n.0",
                currency=Currency.USD,
                exchange=Venue.CBOT,
                fees=0.85, 
                quantity_multiplier=5000,
                price_multiplier=0.01, 
                initialMargin=2056.75,
                product_code="ZC",
                product_name="Corn",
                industry=Industry.AGRICULTURE,
                contract_size=5000,
                contract_units=ContractUnits.BUSHELS,
                tick_size=0.0025,
                min_price_fluctuation=12.50,
                continuous=True,
                lastTradeDateOrContractMonth="202404")
        
        database.create_symbol(future)
        
        print("Successfully created symbol.")
    except Exception as e:
        raise Exception(f"Erro creating symbol: {e}")

# Examples
# --------
# equity=Equity(
#     ticker="AAPL22",
#     security_type=SecurityType.STOCK,
#     company_name="Apple Inc.",
#     venue=Venue.NASDAQ,
#     currency=Currency.USD,
#     industry=Industry.TECHNOLOGY,
#     market_cap=2000000000000.00,
#     shares_outstanding=5000000000
# )
# database.create_symbol(equity)

# future=Future(
#     ticker = "HE.n.0",
#     security_type = SecurityType.FUTURE,
#     product_code="HE",
#     product_name="Lean Hogs",
#     venue=Venue.CME,
#     currency=Currency.USD,
#     industry=Industry.AGRICULTURE,
#     contract_size=40000,
#     contract_units=ContractUnits.POUNDS,
#     tick_size=0.00025,
#     min_price_fluctuation=10,
#     continuous=True
# )
# database.create_symbol(future)

# future=Future(
#     ticker = "ZC.n.0",
#     security_type = SecurityType.FUTURE,
#     product_code="ZC",
#     product_name="Corn",
#     venue=Venue.CME,
#     currency=Currency.USD,
#     industry=Industry.AGRICULTURE,
#     contract_size=5000,
#     contract_units=ContractUnits.BUSHELS,
#     tick_size=0.0025,
#     min_price_fluctuation=12.50,
#     continuous=True
# )
# database.create_symbol(future)

# option=Option(
#     ticker = "AAPLPRT",
#     security_type = SecurityType.OPTION, 
#     strike_price=109.99,
#     currency=Currency.USD,
#     venue=Venue.NASDAQ,
#     expiration_date="2024-01-01",
#     option_type="CALL",
#     contract_size=100,
#     underlying_name="AAPL Inc"
# )
# database.create_symbol(option)

# index=Index(ticker="^GSPC",
#                     security_type=SecurityType.INDEX,
#                     name="S&P 500",
#                     currency=Currency.USD,
#                     asset_class=AssetClass.EQUITY,
#                     venue= Venue.NASDAQ)

# database.create_symbol(index)


# ZM_n_0 = {
#     'ticker':'ZM.n.0',
#     'security_type':SecurityType.FUTURE,
#     'product_code':'ZM',
#     'product_name':'Soybean Meal',
#     'exchange':Exchange.CME,
#     'currency':Currency.USD,
#     'contract_size':100,
#     'contract_units':ContractUnits.SHORT_TON,
#     'tick_size':0.10,
#     'min_price_fluctuation':10.00,
#     'continuous':True
#     }
# database.create_future(**ZM_n_0)
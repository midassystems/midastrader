import json
import requests
import pandas as pd
from enum import Enum
from decouple import config
from ..client import DatabaseClient, SecurityType, Exchange,Indsutry, Currency, ContractUnits, AssetClass


DATABASE_KEY = config('MIDAS_API_KEY')
DATABASE_URL = config('MIDAS_URL')


if __name__ == "__main__":
    # Initialize the database client
    database = DatabaseClient(DATABASE_KEY,DATABASE_URL)

# *** Currency ***
    # -- Create --
    # USD = {
    #     'code':Curency.USD,
    #     'name':'Canadian Dollar',
    #     'region':'Canada',
    #     }
    # database.create_currency(**USD)

    # -- Get All --
    # response = database.get_currencies()
    # print(response)

    # -- Update --
    # updates = {
    #     "code" : "TES", 
    #     "name" : " Tester", 
    #     "region" : "testing"

    # }
    # response = database.update_currency(currency_id=1,**updates)
    # print(response)


# *** Asset Class ***
    # -- Create -- 
    # EQUITY = {
    #         'name':'FIXED INCOME', 
    #         'description':'General fixed income type.'
    #        }
    # database.create_asset_class(**EQUITY)
    
    # -- Get All -- 
    # response = database.get_asset_classes()
    # print(response)

    # -- Update --
    # updates = {
    #     "name" : "TESTING",
    #     "description" : "testing"

    # }
    # response = database.update_asset_class(asset_class_id=1,**updates)
    # print(response)


# *** Index ***
    # -- Create -- 
    # GSPC = {
    #     'ticker':'^GSPC',
    #     'name':'S&P 500',
    #     'currency':Currency.USD,
    #     'security_type':SecurityType.INDEX,
    #     'asset_class': AssetClass.EQUITY
    #     }

    # database.create_index(**GSPC)

    # -- Get -- 
    # response = database.get_indexes()
    # print(response)

    # -- Update -- 
    # updates = {
    #     'ticker':'^GSPC2',
    #     'name':'S&P 600',
    #     'currency':Currency.CAD.value,
    #     'asset_class': AssetClass.COMMODITY.value

    # }
    # response = database.update_index(index_id=1,**updates)
    # print(response)

# *** Equity ***
    # -- Create --
    # AAPL = {
    #     'ticker':'AAPL',
    #     'security_type':SecurityType.EQUITY,
    #     'company_name':'Apple Inc.',
    #     'exchange':Exchange.NASDAQ,
    #     'currency':Currency.USD,
    #     'industry':Indsutry.TECHNOLOGY,
    #     'market_cap':100000,
    #     'shares_outstanding':10000000
    #     }

    # database.create_equity(**AAPL)

    # -- Get -- 
    # response = database.get_equity()
    # print(response)

    # -- Update --
    # updates = {
    #     'symbol_data': {
    #         'ticker':'AAPL2', 
    #         'security_type':SecurityType.EQUITY.value
    #     },
    #     'company_name':'TSLA Inc.',
    #     'currency':Currency.USD.value,
    #     'industry':Indsutry.MATERIALS.value,
    #     }

    # response = database.update_equity(equity_id=1,**updates)
    # print(response)


# *** Future *** 
    # -- Create -- 
    # HE_n_0 = {
    #     'ticker':'HE.n.0',
    #     'security_type':SecurityType.FUTURE,
    #     'product_code':'HE',
    #     'product_name':'Lean Hogs',
    #     'exchange':Exchange.CME,
    #     'currency':Currency.USD,
    #     'contract_size':40000,
    #     'contract_units':ContractUnits.POUNDS,
    #     'tick_size':0.00025,
    #     'min_price_fluctuation':10.00,
    #     'continuous':True
    #     }
    # database.create_future(**HE_n_0)

    # -- Get -- 
    # response = database.get_future()
    # print(response)

    # -- Update --
    # updates = {
    #     'ticker':'HE.n.0',
    #     'product_code':'HE2',
    #     'product_name':'Lea22n Hogs',
    #     'exchange':Exchange.NASDAQ.value,
    #     'currency':Currency.CAD.value,
    #     'contract_size':70000,
    #     'contract_units':ContractUnits.BARRELS.value,
    #     'tick_size':0.39,
    #     'min_price_fluctuation':100.00,
    #     'continuous':False
    #     }

    # response = database.update_future(future_id=1,**updates)
    # print(response)

# *** Symbol *** 
    # -- Get All --
    # response = database.get_symbol()
    # print(response)

    # -- Get -- 
    # ticker = 'AAPL'
    # response = database.get_symbol_by_ticker(ticker)
    # print(response)
    
    
# *** BarData ***
    # -- Create Single -- 
    # data = {
    #     'symbol': "^GSPC",        
    #     "timestamp": "2024-01-02",  # Assuming timestamp is a string; adjust the type as needed
    #     "open": 100.0,
    #     "close": 100.0,
    #     "high": 100.0,
    #     "low": 100.0,
    #     "volume": 10000,  # Adjust types based on your specific requirements
    #     }
    # response = database.create_bar_data(**data)
    
    # -- Create Batch --
    # data = [
    #         {
    #             "symbol": "AAPL", 
    #             "timestamp": "2024-02-01T00:00:00Z", 
    #             "open": 150.0,
    #             "high": 155.0, 
    #             "low": 149.0, 
    #             "close": 154.0, 
    #             "volume": 5000
    #         },
    #         {
    #             "symbol": "HE.n.0", 
    #             "timestamp": "2024-02-01T00:00:00Z", 
    #             "open": 220.0, 
    #             "high": 225.0, 
    #             "low": 219.0, 
    #             "close": 224.0, 
    #             "volume": 3000
    #         }
    #     ]
    # response = database.create_bulk_price_data(data)

    # -- Get Filter-- 
    tickers = ['ZC.n.0']
    start_date = "2024-01-01"
    end_date="2024-03-21"
    response = database.get_bar_data(tickers, start_date, end_date)
    print(response)


    # -- Update -- 
    # ## Not working
    # updates = {
    #     'symbol': "^GSPC",        
    #     "timestamp": "2024-01-02",  # Assuming timestamp is a string; adjust the type as needed
    #     "open": 200.0,
    #     "close": 200.0,
    #     "high": 200.0,
    #     "low": 200.0,
    #     "volume": 9555,  # Adjust types based on your specific requirements
    #     }

    # response = database.update_bar_data(bar_id=1,**updates)
    # print(response)
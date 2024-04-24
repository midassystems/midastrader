import pandas as pd
from decouple import config

from client.client import DatabaseClient
from shared.market_data import BarData, dataframe_to_bardata
from client.sources.databento import DatabentoClient, Schemas, Datasets, Symbology
from shared.symbol import SecurityType, Venue, Industry ,Currency, ContractUnits, Equity

pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000) # Adjust the width of the display in characters
pd.set_option('display.max_rows', None)

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

DATABENTO_API_KEY=config('DATABENTO_API_KEY')

if __name__ == "__main__":
    # Initialize the database client
    database=DatabaseClient(DATABASE_KEY,DATABASE_URL)  # Adjust URL if not running locally

    # Parameters
    symbols=['HE.n.0', 'ZC.n.0'] # 'n' Will rank the expirations by the open interest at the previous day's close
    schema=Schemas.OHLCV_1h
    dataset=Datasets.CME
    stype=Symbology.CONTINUOSCONTRACT
    start_date="2024-01-07T12:00:00"
    end_date="2024-03-20T12:10:00"

    # Check and create assets if they don't exist
    for symbol in symbols:
        if not database.get_symbol_by_ticker(symbol):
            raise Exception(f"{symbol} not present in database.")
        

    # Databento client
    client=DatabentoClient(DATABENTO_API_KEY)
    response=client.get_historical_bar(dataset, symbols, schema, stype, start_date, end_date)
    
    # Convert DataFrame to list of BarData
    df = response.to_df(pretty_ts=False,price_type='decimal')
    bardata_list=dataframe_to_bardata(df)
    print(bardata_list)

    # Add to database
    database_response=database.create_bulk_price_data(bardata_list)
    print(database_response)
    
# # -- Get Databento Equtiy Data --
# symbols = ['AAPL', 'MSFT']
# schema = Schemas.OHLCV_1h
# dataset = Datasets.NASDAQ
# stype = Symbology.RAWSYMBOL

# # -- Get Databento Future Data by Contract Symbol --
# schema = Schemas.OHLCV_1d
# dataset = Datasets.CME
# stype = Symbology.RAWSYMBOL
# symbols = ["ZCH4"] 
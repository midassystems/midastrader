import pandas as pd
from enum import Enum
import databento as db
from decouple import config
from datetime import datetime, timedelta

pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000) # Adjust the width of the display in characters
pd.set_option('display.max_rows', None)

class Schemas(Enum):
    MBO='mbo'               # Market by order, full order book, tick data
    MBP_10='mbp-10'	        # L2, market by price, market depth
    MBP_1='mbp-1'	        # L1, top of book, trades and quotes
    TBBO='tbbo'	            # Top of book, sampled in trade space
    Trades='trades'	        # Last sale, time and sales, tick-by-tick trades
    OHLCV_1s='ohlcv-1s'     # OHLCV bars, aggregates
    OHLCV_1m='ohlcv-1m'     # OHLCV bars, aggregates
    OHLCV_1h='ohlcv-1h'     # OHLCV bars, aggregates
    OHLCV_1d='ohlcv-1d'     # OHLCV bars, aggregates
    Definition='definition'	# Security definitions, reference data, symbol list
    Imbalance='imbalance'	# Imbalance auction quotes
    Statistics='statistics' 

class Symbology(Enum):
    RAWSYMBOL='raw_symbol'         # Original string symbols used by the publisher in the source data.
    INSTRUMENT_ID='instrument_id'  # Unique numeric ID assigned to each instrument by the publisher.
    PARENTSYMBOL='parent'          # Groups instruments related to the market for the same underlying.
    CONTINUOSCONTRACT='continuous' # Proprietary symbology that specifies instruments based on certain systematic rules.

class Datasets(Enum):   
    NASDAQ='XNAS.ITCH'               # Nasdaq TotalView-ITCH is the proprietary data feed that provides full order book depth for Nasdaq market participants.
    CME='GLBX.MDP3'                  # MDP 3.0 is the sole data feed for all instruments traded on CME Globex, including futures, options, spreads and combinations.
    OPRA='OPRA.PILLAR'               # Options data. Consolidated last sale, exchange BBO and national BBO across all US equity options exchanges
    DATABENTOEQUITIES='DBEQ.BASIC'   # A consolidation of US equities prop feeds that’s free to license for all use cases. 
    
class DatabentoClient:
    def __init__(self, api_key:str):
        self.hist_client = db.Historical(api_key)
        self.live_client = db.Live(api_key)

    def get_size(self, dataset: Datasets, symbols:list, schema:Schemas, stype:Symbology, start_date:str, end_date:str) -> float:
        """ Returns data size in GBs."""
        try:
            size = self.hist_client.metadata.get_billable_size(
                dataset=dataset.value,
                symbols=symbols,
                schema=schema.value,
                start=start_date,
                end=end_date,
                stype_in=stype.value,
            )
            # logger.info(f"\n Bytes: {size} | KB:{size/10**3} | MB: {size/10**6} | GB: {size/10**9}\n")
            return size/10**9
        except Exception as e:
            raise Exception(f"Error retrieving request cost: {e}")

    def get_cost(self, dataset: Datasets, symbols:list, schema:Schemas, stype:Symbology, start_date:str, end_date:str) -> float:
        """ Cost returned in USD."""

        try:
            cost = self.hist_client.metadata.get_cost(
                dataset=dataset.value,
                symbols=symbols,
                schema=schema.value,
                start=start_date,
                end=end_date,
                stype_in=stype.value,
            )

            return cost
        except Exception as e:
            raise Exception(f"Error retrieving request cost: {e}")

    def _cost_check(self, dataset: Datasets, symbols:list, schema:Schemas, stype:Symbology, start_date:str, end_date:str) -> float:
        # Get the cost of data pull
        cost = self.get_cost(dataset, symbols, schema, stype, start_date, end_date)

        # Confirm cost with the user, with a maximum of 3 attempts to avoid infinite loop
        max_attempts = 3
        for attempt in range(max_attempts):
            answer = input(f"\nThe cost of this data pull will be ${cost}. Would you like to proceed? (Y/n): ")
            if answer in ['n', 'N']:
                print("Data pull cancelled by user.")
                return False
            elif answer in ['y', 'Y']:
                return True
            else:
                print("Invalid input. Please enter 'Y' to proceed or 'n' to cancel.")
                if attempt == max_attempts - 1:
                    print("Maximum attempts reached. Data pull cancelled.")
                    return False
                
        # def _size_check(self):
            # Check the size of the data
            # If less than 5 GB, proceed with historical data retrieval
            # if self.get_size() < 5:
            #     if self.schema == Schemas.Trades.value:
            #         return self.get_historical_trades()
            #     else:
            #         return self.get_historical_bar()
            # else:
            #     # Suggest batch load for large data sizes
            #     print("\nData size greater than 5 GB: Batch Load Recommended.")
            #     # Here you can add logic for batch loading if applicable

    def resample_trades_to_ohlcv(self, data: db.DBNStore):

        if data.schema != "trades":
            raise ValueError(f"data must be DBNStore object with schema=trades")

        try:
            trades_data = data.to_df()

            ohlcv_data = (
                trades_data
                .groupby(["symbol"])
                .resample("1min")["price"].ohlc()
            )

            return ohlcv_data
        except Exception as e:
            raise Exception(f"Error converting trades to bar data {e}")
        
    def get_historical_bar(self, dataset: Datasets, symbols:list, schema:Schemas, stype:Symbology, start_date:str, end_date:str) -> db.DBNStore:
        """ Used to return smaller batches of data under """              
        
        # if schema not in [Schemas.OHLCV_1s, Schemas.OHLCV_1m, Schemas.OHLCV_1h, Schemas.OHLCV_1d]:
        #     raise TypeError(f"schema but be of type OHLCV_xx")
        try:
            check=self._cost_check(dataset, symbols, schema, stype, start_date, end_date)

            if check:
                data = self.hist_client.timeseries.get_range(
                    dataset=dataset.value,
                    symbols=symbols,
                    schema=schema.value,
                    stype_in=stype.value,
                    start=start_date,
                    end=end_date
                )

                return data
        except Exception as e:
            raise Exception(f"Error retrieving historical data: {e}")
    
    def get_historical_tbbo(self, dataset: Datasets, symbols:list,stype:Symbology, start_date:str, end_date:str) -> db.DBNStore:
        
        schema=Schemas.Trades
        self._cost_check(dataset, symbols, schema, stype, start_date, end_date)

        data = self.hist_client.timeseries.get_range(
            dataset=dataset.value,
            symbols=symbols,
            schema=schema.value,
            stype_in=stype.value,
            start=start_date,
            end=end_date

        )
        return data
    
    # def get_batch(self):
    #     data = self.hist_client.batch.submit_job(
    #         dataset=self.datasets,
    #         symbols=self.symbols,
    #         schema=self.schemas,
    #         encoding="dbn",
    #         start=self.start_date,
    #         end=self.end_date,
    #     )



# OHLCV
#                            rtype  publisher_id  instrument_id    open    high     low   close  volume  symbol
# ts_event                                                                                                     
# 2024-02-06 12:00:00+00:00     33             1         243778  443.50  443.75  443.50  443.75      20  ZC.n.0
# 2024-02-06 12:01:00+00:00     33             1         243778  443.50  443.50  443.50  443.50      11  ZC.n.0
# 2024-02-06 12:02:00+00:00     33             1         243778  443.50  443.50  443.50  443.50     100  ZC.n.0
# 2024-02-06 12:03:00+00:00     33             1         243778  443.50  443.75  443.50  443.75      27  ZC.n.0
# 2024-02-06 12:06:00+00:00     33             1         243778  443.50  443.50  443.50  443.50      10  ZC.n.0

# Trades
#                                                                ts_event  rtype  publisher_id  instrument_id action side  depth   price  size  flags  ts_in_delta  sequence  symbol
# ts_recv                                                                                                                                                                           
# 2024-02-06 12:00:29.132952677+00:00 2024-02-06 12:00:29.132637997+00:00      0             1         243778      T    B      0  443.50     2      0        15709  16910303  ZC.n.0
# 2024-02-06 12:00:29.133817907+00:00 2024-02-06 12:00:29.132917611+00:00      0             1         243778      T    B      0  443.50     3      0        14144  16910347  ZC.n.0
# 2024-02-06 12:00:29.133848318+00:00 2024-02-06 12:00:29.132954839+00:00      0             1         243778      T    B      0  443.50     5      0        14138  16910349  ZC.n.0
# 2024-02-06 12:00:29.133968123+00:00 2024-02-06 12:00:29.132967857+00:00      0             1         243778      T    B      0  443.50     5      0        13082  16910355  ZC.n.0


# TBBO
#                                                                ts_event  rtype  publisher_id  instrument_id action side  depth   price  size  flags  ts_in_delta  sequence  bid_px_00  ask_px_00  bid_sz_00  ask_sz_00  bid_ct_00  ask_ct_00  symbol
# ts_recv                                                                                                                                                                                                                                             
# 2024-02-06 12:00:29.132952677+00:00 2024-02-06 12:00:29.132637997+00:00      1             1         243778      T    B      0  443.50     2      0        15709  16910303     443.25     443.50        155         15         27          3  ZC.n.0
# 2024-02-06 12:00:29.133817907+00:00 2024-02-06 12:00:29.132917611+00:00      1             1         243778      T    B      0  443.50     3      0        14144  16910347     443.25     443.50        155         13         27          2  ZC.n.0
# 2024-02-06 12:00:29.133848318+00:00 2024-02-06 12:00:29.132954839+00:00      1             1         243778      T    B      0  443.50     5      0        14138  16910349     443.25     443.50        155         10         27          2  ZC.n.0
# 2024-02-06 12:00:29.133968123+00:00 2024-02-06 12:00:29.132967857+00:00      1             1         243778      T    B      0  443.50     5      0        13082  16910355     443.25     443.50        155          5         27          2  ZC.n.0
# 2024-02-06 12:00:29.137096115+00:00 2024-02-06 12:00:29.135514715+00:00      1             1         243778      T    A      0  443.50     3      0        13716  16910542     443.50     443.75          3        171          1         26  ZC.n.0
# 2024-02-06 12:00:29.139255243+00:00 2024-02-06 12:00:29.138307997+00:00      1             1         243778      T    A      0  443.50     1      0        17272  16910664     443.50     443.75          1        169          1         25  ZC.n.0

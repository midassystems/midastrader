from decouple import config
from ..client import DatabaseClient 
from ...shared.data import Currency, AssetClass, SecurityType, Industry, Venue, ContractUnits

DATABASE_KEY = config('LOCAL_API_KEY')
DATABASE_URL = config('LOCAL_URL')

if __name__ == "__main__":
        
    database = DatabaseClient(DATABASE_KEY,DATABASE_URL)
    
    try:
        # Create Currencies
        database.create_currency(Currency.USD)
        database.create_currency(Currency.EUR)
        database.create_currency(Currency.GBP)
        database.create_currency(Currency.JPY)
        database.create_currency(Currency.AUD)
        database.create_currency(Currency.CAD)

        # Create Asset Classes
        database.create_asset_class(AssetClass.EQUITY)
        database.create_asset_class(AssetClass.COMMODITY)
        database.create_asset_class(AssetClass.FIXED_INCOME)
        database.create_asset_class(AssetClass.FOREX)
        database.create_asset_class(AssetClass.CRYPTOCURRENCY)

        # Create Security Types
        database.create_security_type(SecurityType.STOCK)
        database.create_security_type(SecurityType.FUTURE)
        database.create_security_type(SecurityType.OPTION)
        database.create_security_type(SecurityType.INDEX)

        # Create Venues
        database.create_venue(Venue.CME)
        database.create_venue(Venue.NASDAQ)
        database.create_venue(Venue.CBOT)
        database.create_venue(Venue.NYSE)

        # Create Industries
        database.create_industry(Industry.AGRICULTURE)
        database.create_industry(Industry.COMMUNICATION)
        database.create_industry(Industry.CONSUMER)
        database.create_industry(Industry.ENERGY)
        database.create_industry(Industry.FINANCIALS)
        database.create_industry(Industry.HEALTHCARE)
        database.create_industry(Industry.INDUSTRIALS)
        database.create_industry(Industry.MATERIALS)
        database.create_industry(Industry.METALS)
        database.create_industry(Industry.REAL_ESTATE)
        database.create_industry(Industry.TECHNOLOGY)
        database.create_industry(Industry.UTILITIES)

        # Create Contact Units
        database.create_contract_units(ContractUnits.BARRELS)
        database.create_contract_units(ContractUnits.BUSHELS)
        database.create_contract_units(ContractUnits.METRIC_TON)
        database.create_contract_units(ContractUnits.POUNDS)
        database.create_contract_units(ContractUnits.TROY_OUNCE)
        database.create_contract_units(ContractUnits.SHORT_TON)

        print("Successfully uploaded to database.")
        
    except Exception as e:
        raise Exception(f"Error with initial database upload: {e}")


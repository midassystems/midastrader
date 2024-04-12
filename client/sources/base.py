from decouple import config
from ..client import DatabaseClient, Currency, AssetClass

DATABASE_KEY = config('MIDAS_API_KEY')
DATABASE_URL = config('MIDAS_URL')

if __name__ == "__main__":
    # Initialize the database client
    database = DatabaseClient(DATABASE_KEY,DATABASE_URL)

    # Create Currencies
    USD = {
        'code': Currency.USD,
        'name': 'US Dollar',
        'region': 'United States',
        }
    database.create_currency(**USD)

    EUR = {
        'code': Currency.EUR, 
        'name': 'Euro', 
        'region': 'European Union'
    }
    database.create_currency(**EUR)

    GBP = {
        'code': Currency.GBP,
        'name': 'Pound Sterling', 
        'region': 'United Kingdom'
    }
    database.create_currency(**GBP)

    JPY = {
        'code': Currency.JPY,
        'name': 'Japanese Yen', 
        'region': 'Japan'
    }
    database.create_currency(**JPY)

    AUD = {
        'code': Currency.AUD, 
        'name': 'Australian Dollar', 
        'region': 'Australia'
    }
    database.create_currency(**AUD)

    CAD = {
        'code': Currency.CAD,
        'name': 'Canadian Dollar',
        'region': 'Canada',
        }
    database.create_currency(**CAD)

    # Create Asset Classes
    EQUITY = {
            'name':AssetClass.EQUITY, 
            'description':'General equity type.'
           }
    database.create_asset_class(**EQUITY)

    COMMODITY = {
        'name':AssetClass.COMMODITY, 
        'description':'General commodity type.'
        }
    database.create_asset_class(**COMMODITY)

    FIXED_INCOME = {
        'name':AssetClass.FIXED_INCOME, 
        'description':'General fixed income type.'
        }
    database.create_asset_class(**FIXED_INCOME)

    FOREX = {
        'name':AssetClass.FOREX, 
        'description':'General forex type.'
        }
    database.create_asset_class(**FOREX)

    CRYPTOCURRENCY = {
        'name':AssetClass.CRYPTOCURRENCY, 
        'description':'General cryptocurrrency type.'
        }
    database.create_asset_class(**CRYPTOCURRENCY)
import requests
from typing import List   

from midas.shared.symbol import *
from midas.shared.market_data import *
from midas.shared.backtest import Backtest
from midas.shared.utils import iso_to_unix, unix_to_iso
from midas.shared.live_session import LiveTradingSession

class DatabaseClient:
    def __init__(self, api_key:str, api_url:str ='http://127.0.0.1:8000'):
        self.api_url = api_url
        self.api_key = api_key

    # -- Symbol Data -- 
    def create_asset_class(self, asset_class: AssetClass):
        """
        Creates a new asset class.

        Parameters:
        - asset_class (AssetClass): The new asset class enum value to create.
        """
        if not isinstance(asset_class, AssetClass):
            raise TypeError(f"asset_class must be of type AssetClass.")
        
        url = f"{self.api_url}/api/asset_class/"
        data = {"value": asset_class.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Asset class creation failed: {response.text}")
        return response.json()
    
    def get_asset_classes(self):
        """
        Retrieves a list of all asset classes.
        """
        url = f"{self.api_url}/api/asset_class/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching asset classes failed: {response.text}")
        return response.json()

    def update_asset_class(self, asset_class_id: int, asset_class: AssetClass):
        """
        Updates an existing asset class.

        Parameters:
        - asset_class_id (int): The ID of the asset class to update.
        - asset_class (AssetClass): The new asset class enum value to update.
        """
        if not isinstance(asset_class, AssetClass):
            raise TypeError(f"asset_class must be of type AssetClass.")

        url = f"{self.api_url}/api/asset_class/{asset_class_id}/"
        data = {"value": asset_class.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Asset class update failed: {response.text}")
        return response.json()

    def delete_asset_class(self, asset_class_id: int):
        """
        Deletes an asset class.

        Parameters:
        - asset_class_id (int): The ID of the asset class to be deleted.
        """
        url = f"{self.api_url}/api/asset_class/{asset_class_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            raise ValueError(f"Asset class delete failed: {response.text}")
        return response.json()
    
    def create_security_type(self, sec_type: SecurityType):
        """
        Creates a new security type.

        Parameters:
        - sec_type (SecurityType): The new security type enum value to create.
        """
        if not isinstance(sec_type, SecurityType):
            raise TypeError(f"sec_type must be of type SecurityType.")

        url = f"{self.api_url}/api/security_type/"
        data = {"value": sec_type.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Security type creation failed: {response.text}")
        return response.json()
    
    def get_security_types(self):
        """
        Retrieves a list of all security types.
        """
        url = f"{self.api_url}/api/security_type/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching security types failed: {response.text}")
        return response.json()

    def update_security_type(self, sec_type_id: int, sec_type: SecurityType):
        """
        Updates an existing security type.

        Parameters:
        - sec_type_id (int): The ID of the security type being updated.
        - sec_type (SecurityType): The new secuirty type enum value to update.
        """
        if not isinstance(sec_type, SecurityType):
            raise TypeError(f"sec_type must be of type SecurityType.")

        url = f"{self.api_url}/api/security_type/{sec_type_id}/"
        data = {"value": sec_type.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Security type update failed: {response.text}")
        return response.json()

    def delete_security_type(self, sec_type_id: int):
        """
        Deletes a security type.

        Parameters:
        - sec_type_id (int): The ID of the security type to be deleted.
        """
        url = f"{self.api_url}/api/security_type/{sec_type_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            raise ValueError(f"Security type delete failed: {response.text}")
        return response.json()
    
    def create_venue(self, venue: Venue):
        """
        Creates a new venue.

        Parameters:
        - venue (Venue): The new venue enum value to be created.
        """
        if not isinstance(venue, Venue):
            raise TypeError(f"venue must be of type Venue.")

        url = f"{self.api_url}/api/venue/"
        data = {"value": venue.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Venue creation failed: {response.text}")
        return response.json()
    
    def get_venues(self):
        """
        Retrieves a list of all venues.
        """
        url = f"{self.api_url}/api/venue/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching venues failed: {response.text}")
        return response.json()

    def update_venue(self, venue_id: int, venue: Venue):
        """
        Updates an existing venue.

        Parameters:
        - venue_id (int): The ID of the venue to be updated.
        - venue (Venue): The new venue enum value to updated.
        """
        if not isinstance(venue, Venue):
            raise TypeError(f"venue must be of type Venue.")

        url = f"{self.api_url}/api/venue/{venue_id}/"
        data = {"value": venue.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Venue update failed: {response.text}")
        return response.json()

    def delete_venue(self, venue_id: int):
        """
        Deletes a venue.

        Parameters:
        - venue_id (int): The ID of the venue to be deleted.
        """
        url = f"{self.api_url}/api/venue/{venue_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            raise ValueError(f"Venue delete failed: {response.text}")
        return response.json()
    
    def create_currency(self, currency: Currency):
        """
        Creates a new currency.

        Parameters:
        - currency (Currency): The new currency enum value to be created.
        """
        if not isinstance(currency, Currency):
            raise TypeError(f"currency must be of type Currency.")

        url = f"{self.api_url}/api/currency/"
        data = {"value": currency.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Currency creation failed: {response.text}")
        return response.json()
    
    def get_currencies(self):
        """
        Retrieves a list of all currencies.
        """
        url = f"{self.api_url}/api/currency/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching currencies failed: {response.text}")
        return response.json()

    def update_currency(self, currency_id: int, currency: Currency):
        """
        Updates an existing currency.

        Parameters:
        - currency_id (int): The ID of the currency to be updated.
        - currency (Currency): The new currency enum value to update.
        """
        if not isinstance(currency, Currency):
            raise TypeError(f"currency must be of type Currency.")

        url = f"{self.api_url}/api/currency/{currency_id}/"
        data = {"value": currency.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Currency update failed: {response.text}")
        return response.json()
    
    def delete_currency(self, currency_id: int):
        """
        Deletes a currency.

        Parameters:
        - currency_id (int): The ID of the currency to be deleted.
        """
        url = f"{self.api_url}/api/currency/{currency_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            raise ValueError(f"Currency delete failed: {response.text}")
        return response.json()
    
    def create_industry(self, industry: Industry):
        """
        Creates a new industry.

        Parameters:
        - industry (Industry): The new industry enum value to create.
        """
        if not isinstance(industry, Industry):
            raise TypeError(f"industry must be of type Industry.")

        url = f"{self.api_url}/api/industry/"
        data = {"value": industry.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Industry creation failed: {response.text}")
        return response.json()
    
    def get_industries(self):
        """
        Retrieves a list of all industries.
        """
        url = f"{self.api_url}/api/industry/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching industries failed: {response.text}")
        return response.json()

    def update_industry(self, industry_id: int, industry: Industry):
        """
        Updates an existing industry.

        Parameters:
        - industry_id (int): The ID of the industry to update.
        - industry (Industry): The new industry enum value to update.
        """
        if not isinstance(industry, Industry):
            raise TypeError(f"industry must be of type Industry.")

        url = f"{self.api_url}/api/industry/{industry_id}/"
        data = {"value": industry.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Industry update failed: {response.text}")
        return response.json()

    def delete_industry(self, industry_id: int):
        """
        Delete an industry.

        Parameters:
        - industry_id (int): The ID of the industry_id to be deleted.
        """
        url = f"{self.api_url}/api/industry/{industry_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            raise ValueError(f"Industry delete failed: {response.text}")
        return response.json()
    
    def create_contract_units(self, contract_units: ContractUnits):
        """
        Creates a new contract_units.

        Parameters:
        - contract_units (ContractUnits): The new contract_units enum value to create.
        """
        if not isinstance(contract_units, ContractUnits):
            raise TypeError(f"contract_units must be of type ContractUnits.")

        url = f"{self.api_url}/api/contract_units/"
        data = {"value": contract_units.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 201:
            raise ValueError(f"Contract units creation failed: {response.text}")
        return response.json()
    
    def get_contract_units(self):
        """
        Retrieves a list of all contract_units.
        """
        url = f"{self.api_url}/api/contract_units/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching contract_units failed: {response.text}")
        return response.json()

    def update_contract_units(self, contract_units_id: int, contract_units: ContractUnits):
        """
        Updates an existing contract unit.

        Parameters:
        - contract_units_id (int): The ID of the contract_units to update.
        - contract_units (ContractUnits): The new contract_units enum value to update.
        """
        if not isinstance(contract_units, ContractUnits):
            raise TypeError(f"contract_units must be of type ContractUnits.")

        url = f"{self.api_url}/api/contract_units/{contract_units_id}/"
        data = {"value": contract_units.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Contract units update failed: {response.text}")
        return response.json()

    def delete_contract_units(self, contract_units_id: int):
        """
        Delete a contract_units.

        Parameters:
        - contract_units_id (int): The ID of the contract_units to be deleted.
        """
        url = f"{self.api_url}/api/contract_units/{contract_units_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.delete(url, headers=headers)

        if response.status_code != 204:
            raise ValueError(f"Contract units delete failed: {response.text}")
        return response.json()
    
    # -- Symbols -- 
    def create_symbol(self, symbol: Symbol):
        """
        Creates a new symbol and a new sub-symbol in the correspomding security type.
            ex. Creating AAPL would result in a new Symbol and Equity object.

        Parameters:
        - symbol (Symbol): Symbol object of the symbol to be created.
        """
        if not isinstance(symbol, Symbol):
            raise TypeError(f"symbol must be of type Symbol.")
        
        url = f"{self.api_url}/api/symbols/"
        data = symbol.to_dict()
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 201:
            raise ValueError(f"Symbol creation failed: {response.text}")
        return response.json()

    def delete_symbol(self, symbol_id: int):
        """
        Deletes a symbol and the security type symbol.
            ex. Deleting AAPL would result in a deletion of a Symbol object and Equity object.

        Parameters:
        - symbol_id (int):  The ID of the symbol to be deleted.
        """
        if not isinstance(symbol_id, int):
            raise TypeError(f"symbol_id must be of type int.")
        
        url = f"{self.api_url}/api/symbols/{symbol_id}/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.delete(url, headers=headers)
        
        if response.status_code != 204:
            raise ValueError(f"Symbol deletion failed: {response.text}")

    def update_symbol(self, symbol_id: int, symbol: Symbol):
        """
        Updates information for an existing symbol. 

        Parameters:
        - symbol_id (int): The ID of the symbol to be updated.
        - symbol (Symbol): Symbol object with updated fields.
        """
        if not isinstance(symbol, Symbol):
            raise TypeError(f"symbol must be of type Symbol.")
        
        url = f"{self.api_url}/api/symbols/{symbol_id}/"
        data = symbol.to_dict()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Symbol update failed: {response.text}")
        return response.json()
    
    def get_symbol_by_ticker(self, ticker: str):
        """
        Retrieves details on a specific symbol.

        Parameters:
        - ticker (str): Ticker of the symbol being retrieved.
        """
        url = f"{self.api_url}/api/symbols/"
        params = {'ticker': ticker}
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise ValueError(f"Failed to retrieve symbol by ticker: {response.text}")
    
    def get_symbols(self):
        """
        Retrieves a list of all symbols.
        """
        url = f"{self.api_url}/api/symbols/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve symbols: {response.text}")
        return response.json()
    
    def get_equity(self):
        """
        Retrieves a list of all equities.
        """
        url = f"{self.api_url}/api/equities/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching benchmarks failed: {response.text}")
        return response.json()

    def get_future(self):
        """
        Retrieves a list of all futures.
        """
        url = f"{self.api_url}/api/futures/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching benchmarks failed: {response.text}")
        return response.json()

    def get_indexes(self):
        """
        Retrieves a list of all indexes.
        """
        url = f"{self.api_url}/api/indexes/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching benchmarks failed: {response.text}")
        return response.json()
    
    # def get_options(self):
        # """
        # Retrieves a list of all equities.
        # """
    #     url = f"{self.api_url}/api/options/"
    #     headers = {
    #         "Content-Type": "application/json",
    #         "Accept": "application/json",
    #         "Authorization": f"Token {self.api_key}"
    #     }
    #     response = requests.get(url, headers=headers)
    #     if response.status_code != 200:
    #         raise ValueError(f"Fetching benchmarks failed: {response.text}")
    #     return response.json()
    

    # -- Bar Data -- 
    def create_bar_data(self, bar: BarData):
        """
        Creates a new bardata object. 
        ** Only creates a single object at a time **

        Parameters:
        - bar (BarData): BarData object to be created.
        """
        if not isinstance(bar, BarData):
            raise TypeError(f"bar must be of type BarData.")
        
        url = f"{self.api_url}/api/bardata/"
        data = bar.to_dict()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)

        # Handle the response
        if response.status_code != 201:
            raise ValueError(f"Bar data creation failed: {response.text}")
        return response.json()

    def create_bulk_price_data(self, bulk_data: List[BarData]):
        """
        Creates multiple bar data objects at a time. Uses batching to not overwhelm the server. 

        Parameters:
        - bulk_data (List[BarData]): List of BarData objects to be created.
        """
        # Convert data to dict
        data = [item.to_dict() for item in bulk_data]

        batch_size = 1000 # 900 
        total_batches = len(data) // batch_size + (1 if len(data) % batch_size > 0 else 0)
        all_responses = []

        for batch_number in range(total_batches):
            # Extract the current batch
            start_index = batch_number * batch_size
            end_index = start_index + batch_size
            current_batch = data[start_index:end_index]

            # Send the batch request
            url = f"{self.api_url}/api/bardata/bulk_create/"
            headers = {'Authorization': f'Token {self.api_key}'}
            response = requests.post(url, json=current_batch, headers=headers)

            if response.status_code != 201:
                raise ValueError(f"Bulk bar data creation failed for batch {batch_number + 1}: {response.text}")
            
            all_responses.append(response.json())

        # Aggregate all responses
        aggregated_response = {
            'total_batches': total_batches,
            'batch_responses': all_responses
        }
        return aggregated_response
    
    def get_bar_data(self, tickers: List[str], start_date: str, end_date: str):
        """
        Retrieves bar data by ticker and time range.  

        Parameters:
        - tickers (list(str)): List if tickers for which data is being retrieved.
        - start_date (str): Start date expected in ISO 8601.
        - end_date (str): End date expected in ISO 8601.
        """
        batch_size = 1000

        # Convert ISO formatted start and end dates to Unix timestamps
        start_unix = iso_to_unix(start_date)
        end_unix = iso_to_unix(end_date)

        current_start_unix = start_unix
        all_data = []

        # Compute batch_size in seconds (batch_size days * 24 hours * 3600 seconds)
        batch_size_nanoseconds = batch_size * 24 * 3600 * int(1e9)

        while current_start_unix < end_unix:
            current_end_unix = min(current_start_unix + batch_size_nanoseconds, end_unix)

            # Fetch batch data using Unix timestamps. Ensure API or data source can handle Unix timestamps
            batch_data = self._fetch_batch_data(tickers, current_start_unix, current_end_unix)
            all_data.extend(batch_data)

            # Set the start of the next batch to the end of the current batch
            current_start_unix = current_end_unix + 1

        return all_data

    def _fetch_batch_data(self, tickers: List[str], start_date:int, end_date:int):
        """
        Exectutes the retrieval requestd for bar data. 
            *** Not intended for external use. Use get_bar_data ***

        Parameters:
        - tickers (list(str)): List if tickers for which data is being retrieved.
        - start_date (int): Start date expected in UNIX format in nanoseconds
        - end_date (int): End date expected in UNIX format in nanoseconds.
        """
        url = f"{self.api_url}/api/bardata/"
        params = {
            'tickers': ','.join(tickers),
            'start_date': start_date,
            'end_date': end_date
        }
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve bar data for batch {start_date} to {end_date}: {response.text}")

        return response.json()
    
    def update_bar_data(self, bar_id: int, bar: BarData):
        """
        Updates information for an bar.

        Parameters:
        - bar_id (int): The ID of the bar to be updated.
        - bar (BarData): BarDara object with updated fields.
        """
        url = f"{self.api_url}/api/bardata/{bar_id}/"
        data = bar.to_dict()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Bar data update failed: {response.text}")
        return response.json()
    
    # -- Backtest Data -- 
    def create_backtest(self, backtest: Backtest):
        """
        Create a new backtest.

        Parameters:
        - backtest (Backtest): Backtest object to be created.
        """
        if not isinstance(backtest, Backtest):
            raise TypeError(f"backtest must be of type Backtest.")
        
        url = f"{self.api_url}/api/backtest/"
        data=backtest.to_dict()

        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Backtest creation failed: {response.text}")
        return response.json()

    def get_backtests(self):
        """
        Retrieves a list of all backtests.
        """
        url = f"{self.api_url}/api/backtest/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers = {'Authorization': f'Token {self.api_key}'})

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve backtests: {response.text}")
        return response.json()

    def get_specific_backtest(self, backtest_id: int):
        """
        Retrieves a specific backtest.

        Parameters:
        - backtest_id (int): ID of the backtest being retrieved.
        """
        url = f"{self.api_url}/api/backtest/{backtest_id}/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve backtest: {response.text}")
        return response.json()

    # -- Regresssion Data --
    def create_regression_analysis(self, regression_results:dict):
        """
        Create a new backtest.

        Parameters:
        - backtest (Backtest): Backtest object to be created.
        """
        if not isinstance(regression_results, dict):
            raise TypeError(f"regression_results must be of type dict.")
        
        url = f"{self.api_url}/api/regression_analysis/"

        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.post(url, json=regression_results, headers=headers)

        if response.status_code != 201:
            raise ValueError(f"Backtest creation failed: {response.text}")
        return response.json()

    # -- Live Session Data -- 
    def create_live_session(self, trading_session: LiveTradingSession):
        """
        Create a new live trading session.

        Parameters:
        - trading_session (LiveTradingSession): LiveTradingSession object to be created.
        """
        if not isinstance(trading_session, LiveTradingSession):
            raise TypeError(f"trading_session must be of type LiveTradingSession.")

        url = f"{self.api_url}/api/live_session/"
        data=trading_session.to_dict()
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"LiveSession creation failed: {response.text}")
        return response.json()

    def get_live_sessions(self):
        """
        Retrieves a list of all trading sessions.
        """
        url = f"{self.api_url}/api/live_session/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve live_sessions: {response.text}")
        return response.json()

    def get_specific_live_session(self, live_session_id: int):
        """
        Retrieves a specific trading session.
        
        Parameters:
        - live_session_id (int): ID of the live sesssion being retrieved.
        """
        url = f"{self.api_url}/api/live_session/{live_session_id}/"
        headers = {'Authorization': f'Token {self.api_key}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve live_session: {response.text}")
        return response.json()

    # -- Live Session --
    def create_session(self, session_id: int):
        """
        Creates session instance for current live session.

        Parameters:
        - session_id (int) : Unique identifier associated with live session.
        """
        url =f"{self.api_url}/api/sessions/"
        data = { "session_id" : session_id }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Session creation failed: {response.text}")
        return response.json()
    
    def delete_session(self, session_id: int):
        """
        Deletes a live session.

        Parameters:
        - session_id (int) : Unique identifier associated with live session.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.delete(url, headers=headers)
        
        if response.status_code != 204:
            raise ValueError(f"Session deletion failed: {response.text}")

    def create_positions(self, session_id: int, data: dict):
        """
        Creates position for a live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        - data (dict): Position data in dictionary.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/positions/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Position creation failed: {response.text}")
        return response.json()
    
    def update_positions(self, session_id: int, data: dict):
        """
        Updates position for a live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        - data (dict): Position data in dictionary.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/positions/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Position update failed: {response.text}")
        return response.json()
    
    def get_positions(self, session_id: int):
        """
        Get position data for live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/positions/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Position get failed: {response.text}")
        return response.json()

    def create_orders(self, session_id: int, data: dict):
        """
        Creates orders for a live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        - data (dict): Orders data in dictionary.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/orders/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Order creation failed: {response.text}")
        return response.json()
    
    def update_orders(self, session_id: int, data: dict):
        """
        Updates orders for a live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        - data (dict): Order data in dictionary.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/orders/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Order update failed: {response.text}")
        return response.json()
    
    def get_orders(self, session_id: int):
        """
        Get orders data for live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/orders/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Order get failed: {response.text}")
        return response.json()

    def create_account(self, session_id: int, data:dict):
        """
        Creates account for a live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        - data (dict): Account data in dictionary.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/account/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 201:
            raise ValueError(f"Order creation failed: {response.text}")
        return response.json()
    
    def update_account(self, session_id: int, data: dict):
        """
        Updates account for a live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        - data (dict): Account data in dictionary.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/account/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Order update failed: {response.text}")
        return response.json()
    
    def get_account(self, session_id: int):
        """
        Get account data for live session.

        Parameters:
        - session_id (int): Unique identifier associated with live session.
        """
        url =f"{self.api_url}/api/sessions/{session_id}/account/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise ValueError(f"Order get failed: {response.text}")
        return response.json()


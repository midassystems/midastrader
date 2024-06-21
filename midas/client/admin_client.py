import requests
from typing import List
from midas.shared.market_data import BarData
from midas.shared.symbol import (
    AssetClass,
    Currency,
    SecurityType,
    ContractUnits,
    Industry,
    Venue,
    Symbol,
)


class AdminDatabaseClient:
    def __init__(self, api_key: str, api_url: str = "http://127.0.0.1:8000"):
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
            raise TypeError("asset_class must be of type AssetClass.")

        url = f"{self.api_url}/api/asset_class/"
        data = {"value": asset_class.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("asset_class must be of type AssetClass.")

        url = f"{self.api_url}/api/asset_class/{asset_class_id}/"
        data = {"value": asset_class.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("sec_type must be of type SecurityType.")

        url = f"{self.api_url}/api/security_type/"
        data = {"value": sec_type.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("sec_type must be of type SecurityType.")

        url = f"{self.api_url}/api/security_type/{sec_type_id}/"
        data = {"value": sec_type.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("venue must be of type Venue.")

        url = f"{self.api_url}/api/venue/"
        data = {"value": venue.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("venue must be of type Venue.")

        url = f"{self.api_url}/api/venue/{venue_id}/"
        data = {"value": venue.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("currency must be of type Currency.")

        url = f"{self.api_url}/api/currency/"
        data = {"value": currency.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("currency must be of type Currency.")

        url = f"{self.api_url}/api/currency/{currency_id}/"
        data = {"value": currency.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("industry must be of type Industry.")

        url = f"{self.api_url}/api/industry/"
        data = {"value": industry.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("industry must be of type Industry.")

        url = f"{self.api_url}/api/industry/{industry_id}/"
        data = {"value": industry.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("contract_units must be of type ContractUnits.")

        url = f"{self.api_url}/api/contract_units/"
        data = {"value": contract_units.value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching contract_units failed: {response.text}")
        return response.json()

    def update_contract_units(
        self, contract_units_id: int, contract_units: ContractUnits
    ):
        """
        Updates an existing contract unit.

        Parameters:
        - contract_units_id (int): The ID of the contract_units to update.
        - contract_units (ContractUnits): The new contract_units enum value to update.
        """
        if not isinstance(contract_units, ContractUnits):
            raise TypeError("contract_units must be of type ContractUnits.")

        url = f"{self.api_url}/api/contract_units/{contract_units_id}/"
        data = {"value": contract_units.value}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            raise TypeError("symbol must be of type Symbol.")

        url = f"{self.api_url}/api/symbols/"
        data = symbol.to_dict()
        headers = {"Authorization": f"Token {self.api_key}"}
        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 201:
            raise ValueError(f"Symbol creation failed: {response.text}")
        return response.json()

    def delete_symbol(self, symbol_id: int):
        """
        Deletes a symbol and the security type symbol.
        ex. Deleting AAPL would result in a deletion of a Symbol and Equity object.

        Parameters:
        - symbol_id (int):  The ID of the symbol to be deleted.
        """
        if not isinstance(symbol_id, int):
            raise TypeError("symbol_id must be of type int.")

        url = f"{self.api_url}/api/symbols/{symbol_id}/"
        headers = {"Authorization": f"Token {self.api_key}"}
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
            raise TypeError("symbol must be of type Symbol.")

        url = f"{self.api_url}/api/symbols/{symbol_id}/"
        data = symbol.to_dict()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
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
        params = {"ticker": ticker}
        headers = {"Authorization": f"Token {self.api_key}"}
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
        headers = {"Authorization": f"Token {self.api_key}"}
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
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
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
            "Authorization": f"Token {self.api_key}",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching benchmarks failed: {response.text}")
        return response.json()

    def get_options(self):
        """
        Retrieves a list of all equities.
        """
        url = f"{self.api_url}/api/options/"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {self.api_key}",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Fetching benchmarks failed: {response.text}")
        return response.json()

    # -- Bar Data --
    def create_bar_data(self, bar: BarData):
        """
        Creates a new bardata object.
        ** Only creates a single object at a time **

        Parameters:
        - bar (BarData): BarData object to be created.
        """
        if not isinstance(bar, BarData):
            raise TypeError("bar must be of type BarData.")

        url = f"{self.api_url}/api/bardata/"
        data = bar.to_dict()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {self.api_key}",
        }
        response = requests.post(url, json=data, headers=headers)

        # Handle the response
        if response.status_code != 201:
            raise ValueError(f"Bar data creation failed: {response.text}")
        return response.json()

    def create_bulk_price_data(self, bulk_data: List[BarData]):
        """
        Creates multiple bar data objects at a time. Uses batching to not overwhelm the
        server.

        Parameters:
        - bulk_data (List[BarData]): List of BarData objects to be created.
        """
        # Convert data to dict
        data = [item.to_dict() for item in bulk_data]

        batch_size = 1000  # 900
        total_batches = len(data) // batch_size + (
            1 if len(data) % batch_size > 0 else 0
        )
        all_responses = []

        for batch_number in range(total_batches):
            # Extract the current batch
            start_index = batch_number * batch_size
            end_index = start_index + batch_size
            current_batch = data[start_index:end_index]

            # Send the batch request
            url = f"{self.api_url}/api/bardata/bulk_create/"
            headers = {"Authorization": f"Token {self.api_key}"}
            response = requests.post(url, json=current_batch, headers=headers)

            if response.status_code != 201:
                raise ValueError(
                    f"Bulk bar data creation failed for batch {batch_number + 1}: {response.text}"
                )

            all_responses.append(response.json())

        # Aggregate all responses
        aggregated_response = {
            "total_batches": total_batches,
            "batch_responses": all_responses,
        }
        return aggregated_response

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
            "Authorization": f"Token {self.api_key}",
        }
        response = requests.patch(url, json=data, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Bar data update failed: {response.text}")
        return response.json()

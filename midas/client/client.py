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

    # -- Bar Data -- 
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


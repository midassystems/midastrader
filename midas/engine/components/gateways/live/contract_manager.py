import logging
from ibapi.contract import Contract
from midas.engine.components.gateways.live.data_client import DataClient


class ContractManager:
    """
    Class for managing contract validation with Interactive Brokers.

    Attributes:
    - client (DataClient): An instance of DataClient used for communication with the IB API.
    - logger (logging.Logger): An instance of Logger for logging messages.
    - validated_contracts (dict): A dictionary to store validated contracts.
    """

    def __init__(self, client_instance: DataClient, logger: logging.Logger):
        """
        Initialize the ContractManager instance.

        Parameters:
        - client_instance (DataClient): An instance of DataClient for communication with the IB API.
        - logger (logging.Logger): An instance of Logger for logging messages.
        """
        self.logger = logger
        self.client = client_instance
        self.app = self.client.app
        self.validated_contracts = (
            {}
        )  # Dictionary to store validated contracts

    def validate_contract(self, contract: Contract) -> bool:
        """
        Validate a contract with Interactive Brokers.

        Parameters:
        - contract (Contract): The contract to be validated.

        Returns:
        - bool: True if the contract is successfully validated, False otherwise.
        """
        if not isinstance(contract, Contract):
            raise ValueError("'contract' must be of type Contract instance.")

        # Check if the contract is already validated
        if self._is_contract_validated(contract):
            self.logger.info(
                f"Contract {contract.symbol} is already validated."
            )
            return True

        # Reset the validation attribute in case it has been used before
        self.app.is_valid_contract = None
        self.app.validate_contract_event.clear()

        # Request contract details from IB
        reqId = self.client._get_valid_id()
        self.app.reqContractDetails(reqId=reqId, contract=contract)
        self.app.validate_contract_event.wait()

        # Store the validated contract if it's valid
        if self.app.is_valid_contract:
            self.validated_contracts[contract.symbol] = contract
            self.logger.info(
                f"Contract {contract.symbol} validated successfully."
            )
        else:
            self.logger.warning(
                f"Contract {contract.symbol} validation failed."
            )

        return self.app.is_valid_contract

    def _is_contract_validated(self, contract: Contract) -> bool:
        """
        Check if a contract has already been validated.

        Parameters:
        - contract (Contract): The contract to check for validation.

        Returns:
        - bool: True if the contract has already been validated, False otherwise.
        """
        return contract.symbol in self.validated_contracts

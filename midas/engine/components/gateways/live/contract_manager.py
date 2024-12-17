from ibapi.contract import Contract
from midas.utils.logger import SystemLogger
from midas.engine.components.gateways.backtest.broker_client import (
    BrokerClient,
)


class ContractManager:
    """
    Manages the validation of contracts with Interactive Brokers.

    Attributes:
        client (BrokerClient): Instance of `BrokerClient` used for communication with the IB API.
        logger (logging.Logger): Logger instance for logging messages.
        validated_contracts (dict): Dictionary storing validated contracts, where keys are contract symbols
            and values are the corresponding `Contract` instances.
    """

    def __init__(self, client_instance: BrokerClient):
        """
        Initializes a `ContractManager` instance.

        Args:
            client_instance (BrokerClient): Instance of `BrokerClient` for communication with the IB API.
        """
        self.logger = SystemLogger.get_logger()
        self.client = client_instance
        self.app = self.client.app
        self.validated_contracts = {}

    def validate_contract(self, contract: Contract) -> bool:
        """
        Validates a contract with Interactive Brokers.

        Behavior:
            - Checks if the contract is already validated.
            - If not validated, sends a request to Interactive Brokers for validation.
            - Updates `validated_contracts` upon successful validation.

        Args:
            contract (Contract): The `Contract` object to be validated.

        Returns:
            bool: `True` if the contract is successfully validated, otherwise `False`.

        Raises:
            ValueError: If the provided `contract` is not an instance of `Contract`.
        """
        if not isinstance(contract, Contract):
            raise ValueError("'contract' must be of type Contract instance.")

        # Check if the contract is already validated
        if self._is_contract_validated(contract):
            self.logger.info(f"Contract {contract.symbol} already validated.")
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
        Checks if a contract has already been validated.

        Args:
            contract (Contract): The `Contract` object to check for validation.

        Returns:
            bool: `True` if the contract has already been validated, otherwise `False`.
        """
        return contract.symbol in self.validated_contracts

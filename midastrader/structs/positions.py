from typing import Optional, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from midastrader.structs.symbol import SecurityType, Symbol, Right


@dataclass
class Impact:
    """
    Represents the financial impact of a position, including margin requirements,
    unrealized profit/loss, liquidation value, and cash flow.

    Attributes:
        margin_required (float): The margin required to hold the position.
        unrealized_pnl (float): The unrealized profit or loss of the position.
        liquidation_value (float): The value of the position upon liquidation.
        cash (float): The current cash value associated with the position.
    """

    margin_required: float
    unrealized_pnl: float
    liquidation_value: float
    cash: float


@dataclass
class Position(ABC):
    """
    An abstract base class representing a trading position.

    This class serves as the foundation for specific position types and calculates
    key metrics like market value, unrealized profit/loss, and margin requirements.

    Attributes:
        action (str): The action associated with the position ('BUY' or 'SELL').
        quantity (int): The number of contracts or shares held.
        avg_price (float): The average price at which the position was acquired.
        market_price (float): The current market price of the instrument.
        price_multiplier (int): Multiplier applied to the price (e.g., futures contract size).
        quantity_multiplier (int): Multiplier applied to the quantity.
        initial_value (Optional[float]): The notional value of the position at its inception.
        initial_cost (Optional[float]): The total cost of acquiring the position.
        market_value (Optional[float]): The current market value of the position.
        unrealized_pnl (Optional[float]): The unrealized profit/loss for the position.
        margin_required (Optional[float]): The margin required to maintain the position.
        liquidation_value (Optional[float]): The liquidation value of the position.
    """

    action: str
    quantity: int
    avg_price: float
    market_price: float
    price_multiplier: int
    quantity_multiplier: int

    initial_value: Optional[float] = field(init=False)
    initial_cost: Optional[float] = field(init=False)
    market_value: Optional[float] = field(init=False)
    unrealized_pnl: Optional[float] = field(init=False)
    margin_required: Optional[float] = field(init=False)
    liquidation_value: Optional[float] = field(init=False)

    def __post_init__(self):
        """
        Validates input types and calculates aggregate fields after initialization.

        Raises:
            TypeError: If any attribute is of an incorrect type.
            ValueError: If `action`, `price_multiplier`, or `quantity_multiplier` values are invalid.
        """
        # Type check
        if not isinstance(self.action, str):
            raise TypeError("'action' must be of type str.")
        if not isinstance(self.avg_price, (int, float)):
            raise TypeError("'avg_price' must be of type int or float.")
        if not isinstance(self.quantity, (float, int)):
            raise TypeError("'quantity' must be of type int or float.")
        if not isinstance(self.price_multiplier, (int, float)):
            raise TypeError("'price_multiplier' must be of type int or float.")
        if not isinstance(self.quantity_multiplier, int):
            raise TypeError("'quantity_multiplier' must be of type int.")
        if not isinstance(self.market_price, (int, float)):
            raise TypeError("'market_price' must be of type int or float.")

        # Value constraints
        if self.action not in ["BUY", "SELL"]:
            raise ValueError("'action' must be either ['BUY','SELL'].")
        if self.price_multiplier <= 0 or self.quantity_multiplier <= 0:
            raise ValueError(
                "'price_multiplier' and 'quantity_multiplier' must be greater than zero."
            )

        # Calculate aggregate fields
        self.calculate_initial_value()
        self.calculate_initial_cost()
        self.calculate_market_value()
        self.calculate_margin_required()
        self.calculate_unrealized_pnl()
        self.calculate_liquidation_value()

    @abstractmethod
    def position_impact(self) -> Impact:
        """
        Calculates and returns the financial impact of the position.

        Returns:
            Impact: A data object containing margin, unrealized PnL, liquidation value, and cash flow.
        """
        pass

    @abstractmethod
    def calculate_initial_value(self) -> None:
        """
        Calculates the initial notional value of the position.
        """
        pass

    @abstractmethod
    def calculate_initial_cost(self) -> None:
        """
        Calculates the intital total cost of acquiring the position.
        """
        pass

    @abstractmethod
    def calculate_market_value(self) -> None:
        """
        Calculates the current market value of the position.
        """
        pass

    @abstractmethod
    def calculate_unrealized_pnl(self) -> None:
        """
        Calculates the unrealized profit/loss of the position.
        """
        pass

    @abstractmethod
    def calculate_margin_required(self) -> None:
        """
        Calculates the margin required to maintain the position.
        """
        pass

    @abstractmethod
    def calculate_liquidation_value(self) -> None:
        """
        Calculates the value of the position upon liquidation.
        """
        pass

    @abstractmethod
    def update(
        self,
        quantity: int,
        avg_price: float,
        market_price: float,
        action: str,
    ) -> Impact:
        """
        Updates the position with new values and recalculates financial metrics.

        Args:
            quantity (int): The new quantity of the position.
            avg_price (float): The updated average price.
            market_price (float): The current market price.
            action (str): The action performed ('BUY' or 'SELL').

        Returns:
            Impact: The updated financial impact of the position.
        """
        pass

    def to_dict(self) -> dict:
        """
        Converts the position attributes into a dictionary.

        Returns:
            dict: A dictionary containing the position's details.
        """
        return {
            "action": self.action,
            "avg_price": self.avg_price,
            "price_multiplier": self.price_multiplier,
            "quantity": self.quantity,
            "quantity_multiplier": self.quantity_multiplier,
            "initial_value": self.initial_value,
            "initial_cost": self.initial_cost,
            "market_price": self.market_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "margin_required": self.margin_required,
            "liquidation_value": self.liquidation_value,
        }

    def pretty_print(self, indent: str = "") -> str:
        """
        Generates a human-readable string representation of the position's details.

        Args:
            indent (str): Optional string for formatting output.

        Returns:
            str: A formatted string with all position details.
        """
        return (
            f"{indent}Action: {self.action}\n"
            f"{indent}Average Price: {self.avg_price}\n"
            f"{indent}Quantity: {self.quantity}\n"
            f"{indent}Price Multiplier: {self.price_multiplier}\n"
            f"{indent}Quantity Multiplier: {self.quantity_multiplier}\n"
            f"{indent}Notional Value: {self.initial_value}\n"
            f"{indent}Initial Cost: {self.initial_cost}\n"
            f"{indent}Market Price: {self.market_price}\n"
            f"{indent}Market Value: {self.market_value}\n"
            f"{indent}Unrealized P&L: {self.unrealized_pnl}\n"
            f"{indent}Liquidation Value: {self.liquidation_value}\n"
            f"{indent}Margin Required: {self.margin_required}\n"
        )


@dataclass
class FuturePosition(Position):
    """
    Represents a futures contract position, including margin requirements and related calculations.

    This class extends the abstract `Position` class and provides concrete implementations
    for calculating initial value, costs, unrealized profit/loss, market value, and more.

    Attributes:
        action (str): The action associated with the position ('BUY' or 'SELL').
        quantity (int): The number of contracts or shares held.
        avg_price (float): The average price at which the position was acquired.
        market_price (float): The current market price of the instrument.
        price_multiplier (int): Multiplier applied to the price (e.g., futures contract size).
        quantity_multiplier (int): Multiplier applied to the quantity.
        initial_value (Optional[float]): The notional value of the position at its inception.
        initial_cost (Optional[float]): The total cost of acquiring the position.
        market_value (Optional[float]): The current market value of the position.
        unrealized_pnl (Optional[float]): The unrealized profit/loss for the position.
        margin_required (Optional[float]): The margin required to maintain the position.
        liquidation_value (Optional[float]): The liquidation value of the position.
        initial_margin (float): The margin required per futures contract.
    """

    initial_margin: float

    def __post_init__(self):
        """
        Validates the `initial_margin` field and initializes the base `Position` class.

        Raises:
            TypeError: If `initial_margin` is not of type int or float.
            ValueError: If `initial_margin` is negative.
        """
        # Type check
        if not isinstance(self.initial_margin, (int, float)):
            raise TypeError("'initial_margin' must be of type int or float.")

        # Value constraints
        if self.initial_margin < 0:
            raise ValueError("'initial_margin' must be non-negative.")

        super().__post_init__()

    def position_impact(self) -> Impact:
        """
        Calculates the financial impact of the position, including margin, unrealized PnL, and cash flows.

        Returns:
            Impact: An `Impact` object containing the position's margin, unrealized PnL, liquidation value, and cash.
        """
        self.calculate_market_value()
        self.calculate_unrealized_pnl()
        self.calculate_liquidation_value()

        return Impact(
            margin_required=self.margin_required,
            unrealized_pnl=self.unrealized_pnl,
            liquidation_value=self.liquidation_value,
            cash=self.initial_cost * -1,
        )

    def calculate_initial_value(self) -> None:
        """
        Calculates the initial notional value of the position.
        """
        self.initial_value = (
            self.avg_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def calculate_initial_cost(self) -> None:
        """
        Calculates the initial margin cost required for the position.
        """
        self.initial_cost = self.initial_margin * abs(self.quantity)

    def calculate_market_value(self) -> None:
        """
        Calculates the current market value of the position based on the market price.
        """
        self.market_value = (
            self.market_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def calculate_unrealized_pnl(self) -> None:
        """
        Calculates the unrealized profit or loss for the position.
        """
        self.unrealized_pnl = (
            (self.market_price - self.avg_price)
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def calculate_margin_required(self) -> None:
        """
        Calculates the margin required to maintain the position.
        """
        self.margin_required = self.initial_margin * abs(self.quantity)

    def calculate_liquidation_value(self) -> None:
        """
        Calculates the liquidation value of the position.
        """
        self.liquidation_value = self.initial_cost + (
            (self.market_price - self.avg_price)
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def update(
        self,
        quantity: int,
        avg_price: float,
        market_price: float,
        action: str,
    ) -> Impact:
        """
        Updates the position with new quantity, price, and action, recalculating all relevant metrics.

        Args:
            quantity (int): The quantity to add or reduce in the position.
            avg_price (float): The new average price for the updated position.
            market_price (float): The current market price.
            action (str): The action taken ('BUY' or 'SELL').

        Returns:
            Impact: The financial impact after updating the position, including realized PnL and cash flows.
        """
        initial_cost = self.initial_cost

        # Intial Value before price change
        initial_value = self.initial_value
        self.market_price = market_price

        # Market Value before quantity change
        self.calculate_market_value()
        initial_market_value = self.market_value

        # Unrealized pnl before position update
        total_unrealized_pnl = initial_market_value - initial_value

        # Update quantity/action/avg_price
        new_quantity = self.quantity + quantity

        if action == self.action:  # Adding to the same position
            new_avg_price = (
                (self.avg_price * self.quantity) + (avg_price * quantity)
            ) / new_quantity
            self.avg_price = new_avg_price
        elif abs(quantity) > abs(self.quantity):  # Flipping position
            self.action = "BUY" if new_quantity > 0 else "SELL"
            self.avg_price = avg_price

        self.quantity = new_quantity

        # Update all relevant fields
        self.calculate_initial_value()
        self.calculate_market_value()
        self.calculate_initial_cost()
        self.calculate_margin_required()
        self.calculate_unrealized_pnl()
        self.calculate_liquidation_value()

        # Initial value after update
        initial_value_after_trade = self.initial_value

        # Market value after update
        initial_market_value_after_trade = self.market_value

        # Unrealized pnl remaining in position
        remaining_unrealized_pnl = (
            initial_market_value_after_trade - initial_value_after_trade
        )

        # PNL Realized in trade
        realized_pnl = total_unrealized_pnl - remaining_unrealized_pnl

        # Portion of initial cost return
        returned_cost = initial_cost - self.initial_cost

        return Impact(
            margin_required=self.margin_required,
            unrealized_pnl=self.unrealized_pnl,
            liquidation_value=self.liquidation_value,
            cash=returned_cost + realized_pnl,
        )

    def to_dict(self) -> dict:
        """
        Converts the `FuturePosition` object into a dictionary.

        Returns:
            dict: A dictionary representation of the position, including the initial margin.
        """
        base_dict = super().to_dict()
        base_dict.update({"initial_margin": self.initial_margin})
        return base_dict

    def pretty_print(self, indent: str = "") -> str:
        """
        Generates a human-readable string representation of the position.

        Args:
            indent (str): Optional string to indent the output for formatting.

        Returns:
            str: A formatted string containing the position details.
        """
        string = super().pretty_print(indent)
        string += f"{indent}Initial Margin': {self.initial_margin}\n"
        return string


@dataclass
class EquityPosition(Position):
    """
    Represents an equity position (e.g., stocks) in a portfolio.

    This class implements position calculations such as market value, unrealized PnL,
    and liquidation value for equity instruments. It extends the abstract `Position` class.

    Attributes:
        action (str): The action associated with the position ('BUY' or 'SELL').
        quantity (int): The number of contracts or shares held.
        avg_price (float): The average price at which the position was acquired.
        market_price (float): The current market price of the instrument.
        price_multiplier (int): Multiplier applied to the price (e.g., futures contract size).
        quantity_multiplier (int): Multiplier applied to the quantity.
        initial_value (Optional[float]): The notional value of the position at its inception.
        initial_cost (Optional[float]): The total cost of acquiring the position.
        market_value (Optional[float]): The current market value of the position.
        unrealized_pnl (Optional[float]): The unrealized profit/loss for the position.
        margin_required (Optional[float]): The margin required to maintain the position.
        liquidation_value (Optional[float]): The liquidation value of the position.
    """

    def position_impact(self) -> Impact:
        """
        Calculates the financial impact of the equity position, including margin, unrealized PnL,
        and cash flows.

        Returns:
            Impact: An `Impact` object containing:
                - margin_required: Margin required for the position (always 0 for equities).
                - unrealized_pnl: Unrealized profit or loss.
                - liquidation_value: Liquidation value of the position.
                - cash: Cash impact, calculated as the negative initial cost.
        """
        self.calculate_market_value()
        self.calculate_unrealized_pnl()
        self.calculate_liquidation_value()

        return Impact(
            margin_required=self.margin_required,
            unrealized_pnl=self.unrealized_pnl,
            liquidation_value=self.liquidation_value,
            cash=self.initial_cost * -1,
        )

    def calculate_initial_value(self) -> None:
        """
        Calculates the initial notional value of the equity position.
        """
        self.initial_value = (
            self.avg_price * self.quantity * self.quantity_multiplier
        )

    def calculate_initial_cost(self) -> None:
        """
        Calculates the initial cost of acquiring the equity position.
        """
        self.initial_cost = self.initial_value

    def calculate_market_value(self) -> None:
        """
        Calculates the current market value of the equity position.
        """
        self.market_value = (
            self.market_price * self.quantity * self.quantity_multiplier
        )

    def calculate_unrealized_pnl(self) -> None:
        """
        Calculates the unrealized profit or loss of the equity position.
        """
        self.unrealized_pnl = (
            self.market_price * self.quantity * self.quantity_multiplier
        ) - self.initial_cost

    def calculate_margin_required(self) -> None:
        """
        Calculates the margin required for the equity position.

        Note:
            Margin is set to zero for equity positions.
        """
        self.margin_required = 0

    def calculate_liquidation_value(self) -> None:
        """
        Calculates the liquidation value of the equity position based on the market price.
        """
        self.liquidation_value = (
            self.market_price * self.quantity * self.quantity_multiplier
        )

    def update(
        self,
        quantity: int,
        avg_price: float,
        market_price: float,
        action: str,
    ) -> Impact:
        """
        Updates the equity position with new quantity, price, and action. Recalculates
        all relevant metrics and returns the financial impact.

        Args:
            quantity (int): The quantity to add or reduce in the position.
            avg_price (float): The new average price for the updated position.
            market_price (float): The current market price of the equity.
            action (str): The action performed ('BUY' or 'SELL').

        Returns:
            Impact: An object containing:
                - margin_required: Updated margin (always 0).
                - unrealized_pnl: Updated unrealized profit or loss.
                - liquidation_value: Updated liquidation value.
                - cash: Cash impact, including realized PnL and cost adjustments.
        """
        initial_cost = self.initial_cost

        # Intial Value before price change
        initial_value = self.initial_value
        self.market_price = market_price

        # Market Value before quantity change
        self.calculate_market_value()
        initial_market_value = self.market_value

        # Unrealized pnl before position update
        total_unrealized_pnl = initial_market_value - initial_value

        # Update quantity/action/avg_price
        new_quantity = self.quantity + quantity
        if action == self.action:  # Adding to the same position
            new_avg_price = (
                (self.avg_price * self.quantity) + (avg_price * quantity)
            ) / new_quantity
            self.avg_price = new_avg_price
        elif abs(quantity) > abs(self.quantity):  # Flipping position
            self.action = "BUY" if new_quantity > 0 else "SELL"
            self.avg_price = avg_price

        self.quantity = new_quantity

        # Update all relevant fields
        self.calculate_initial_value()
        self.calculate_market_value()
        self.calculate_initial_cost()
        self.calculate_margin_required()
        self.calculate_unrealized_pnl()
        self.calculate_liquidation_value()

        # Initial value after update
        initial_value_after_trade = self.initial_value

        # Market value after update
        initial_market_value_after_trade = self.market_value

        # Unrealized pnl remaining in position
        remaining_unrealized_pnl = (
            initial_market_value_after_trade - initial_value_after_trade
        )

        # PNL Rrealized in trade
        realized_pnl = total_unrealized_pnl - remaining_unrealized_pnl

        # Portion of initial cost return
        returned_cost = initial_cost - self.initial_cost

        return Impact(
            margin_required=self.margin_required,
            unrealized_pnl=self.unrealized_pnl,
            liquidation_value=self.liquidation_value,
            cash=returned_cost + realized_pnl,
        )

    def to_dict(self) -> dict:
        """
        Converts the `EquityPosition` object into a dictionary.

        Returns:
            dict: A dictionary representation of the position attributes.
        """
        base_dict = super().to_dict()
        return base_dict

    def pretty_print(self, indent: str = "") -> str:
        """
        Generates a human-readable string representation of the equity position.

        Args:
            indent (str): Optional string for formatting the output.

        Returns:
            str: A formatted string containing the position details.
        """
        return super().pretty_print(indent)


@dataclass
class OptionPosition(Position):
    """
    Represents an options position, including specific attributes like option type,
    strike price, and expiration date.

    This class extends the abstract `Position` class and implements calculations for
    market value, unrealized profit/loss, and position updates for options.

    Attributes:
        action (str): The action associated with the position ('BUY' or 'SELL').
        quantity (int): The number of contracts or shares held.
        avg_price (float): The average price at which the position was acquired.
        market_price (float): The current market price of the instrument.
        price_multiplier (int): Multiplier applied to the price (e.g., futures contract size).
        quantity_multiplier (int): Multiplier applied to the quantity.
        initial_value (Optional[float]): The notional value of the position at its inception.
        initial_cost (Optional[float]): The total cost of acquiring the position.
        market_value (Optional[float]): The current market value of the position.
        unrealized_pnl (Optional[float]): The unrealized profit/loss for the position.
        margin_required (Optional[float]): The margin required to maintain the position.
        liquidation_value (Optional[float]): The liquidation value of the position.
        type (Right): The option type ('CALL' or 'PUT').
        strike_price (float): The strike price of the option.
        expiration_date (str): The expiration date of the option in YYYY-MM-DD format.
    """

    type: Right
    strike_price: float
    expiration_date: str = ""

    def __post_init__(self):
        """
        Validates the type, strike price, and expiration date fields.

        Raises:
            TypeError: If `type`, `strike_price`, or `expiration_date` have invalid types.
            ValueError: If `strike_price` is less than or equal to zero.
        """
        # Type Check
        if not isinstance(self.type, Right):
            raise TypeError("'type' must be of type Right enum.")
        if not isinstance(self.strike_price, (int, float)):
            raise TypeError("'strike_price' must be of type int or float.")
        if not isinstance(self.expiration_date, str):
            raise TypeError("'expiration_date' must be of type str.")

        # Value Constraint
        if self.strike_price <= 0:
            raise ValueError("'strike_price' must be greater than zero.")

        super().__post_init__()

    def position_impact(self) -> Impact:
        """
        Calculates the financial impact of the option position, including margin,
        unrealized PnL, and cash flow.

        Returns:
            Impact: An `Impact` object with margin_required, unrealized_pnl,
                    liquidation_value, and cash impact.
        """
        self.calculate_market_value()
        self.calculate_unrealized_pnl()
        self.calculate_liquidation_value()

        return Impact(
            margin_required=self.margin_required,
            unrealized_pnl=self.unrealized_pnl,
            liquidation_value=self.liquidation_value,
            cash=self.initial_cost * -1,
        )

    def calculate_initial_value(self) -> None:
        """
        Calculates the initial notional value of the options position.
        """
        self.initial_value = (
            self.avg_price
            * self.quantity_multiplier
            * self.price_multiplier
            * self.quantity
        )

    def calculate_initial_cost(self) -> None:
        """
        Calculates the initial cost of the options position, adjusting for action (BUY/SELL).
        """
        initial_cost = (
            self.avg_price
            * self.quantity_multiplier
            * self.price_multiplier
            * self.quantity
        )

        # Determine if buying or selling to adjust the initial cost sign
        if self.action == "BUY":
            self.initial_cost = -initial_cost
        elif self.action == "SELL":
            self.initial_cost = initial_cost

    def calculate_market_value(self) -> None:
        """
        Calculates the current market value of the options position.
        """
        self.market_value = (
            self.market_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def calculate_unrealized_pnl(self) -> None:
        """
        Calculates the unrealized profit or loss for the options position based on action.
        """
        if self.action == "BUY":
            self.unrealized_pnl = (
                (self.market_price - self.avg_price)
                * self.price_multiplier
                * self.quantity
                * self.quantity_multiplier
            )
        elif self.action == "SELL":
            self.unrealized_pnl = (
                (self.avg_price - self.market_price)
                * self.price_multiplier
                * self.quantity
                * self.quantity_multiplier
            )
        else:
            raise ValueError("Invalid action type. Must be 'BUY' or 'SELL'.")

    def calculate_margin_required(self) -> None:
        """
        Calculates the margin required for the options position.

        Note:
            Margin is set to zero for options positions.
        """
        self.margin_required = 0

    def calculate_liquidation_value(self) -> None:
        """
        Calculates the liquidation value of the options position.
        """
        self.liquidation_value = (
            self.market_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def update(self, quantity: int, price: float, action: str) -> Impact:
        """
        Updates the options position with new quantity, price, and action. Recalculates
        all relevant metrics and returns the financial impact.

        Args:
            quantity (int): The quantity to add or reduce in the position.
            price (float): The updated market price of the option.
            action (str): The action taken ('BUY' or 'SELL').

        Returns:
            Impact: The updated financial impact of the position.
        """
        initial_cost = self.initial_cost

        # Intial Value before price change
        initial_value = self.initial_value
        self.market_price = price

        # Market Value before quantity change
        self.calculate_market_value()
        initial_market_value = self.market_value

        # Unrealized pnl before position update
        total_unrealized_pnl = initial_market_value - initial_value

        # Update quantity/action/avg_price
        new_quantity = self.quantity + quantity
        if action == self.action:  # Adding to the same position
            new_avg_price = (
                (self.avg_price * self.quantity) + (price * quantity)
            ) / new_quantity
            self.avg_price = new_avg_price
        elif abs(quantity) > abs(self.quantity):  # Flipping position
            self.action = "BUY" if new_quantity > 0 else "SELL"
            self.avg_price = price

        self.quantity = new_quantity

        # Update all relevant fields
        self.calculate_initial_value()
        self.calculate_market_value()
        self.calculate_initial_cost()
        self.calculate_margin_required()
        self.calculate_unrealized_pnl()
        self.calculate_liquidation_value()

        # Initial value after update
        initial_value_after_trade = self.initial_value

        # Market value after update
        initial_market_value_after_trade = self.market_value

        # Unrealized pnl remaining in position
        remaining_unrealized_pnl = (
            initial_market_value_after_trade - initial_value_after_trade
        )

        # PNL Rrealized in trade
        realized_pnl = total_unrealized_pnl - remaining_unrealized_pnl

        # Portion of initial cost return
        returned_cost = initial_cost - self.initial_cost

        return Impact(
            margin_required=self.margin_required,
            unrealized_pnl=self.unrealized_pnl,
            liquidation_value=self.liquidation_value,
            cash=returned_cost + realized_pnl,
        )

    def to_dict(self) -> dict:
        """
        Converts the options position into a dictionary representation.

        Returns:
            dict: A dictionary containing all position details, including options-specific fields.
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "strike_price": self.strike_price,
                "expiration_date": self.expiration_date,
                "type": self.type.value,
            }
        )
        return base_dict

    def pretty_print(self, indent: str = "") -> str:
        """
        Generates a human-readable string representation of the options position.

        Args:
            indent (str): Optional indentation string for formatting.

        Returns:
            str: A formatted string containing the options position details.
        """
        string = super().pretty_print(indent)
        string += f"{indent}Strike Price: {self.strike_price}\n"
        string += f"{indent}Expiration date: {self.expiration_date}\n"
        string += f"{indent}Type: {self.type.value}\n"
        return string


def position_factory(
    asset_type: SecurityType,
    symbol: Symbol,
    **kwargs,
) -> Position:
    """
    Factory function for creating position objects based on the asset type.

    Args:
        asset_type (SecurityType): The type of asset (e.g., STOCK, OPTION, FUTURE).
        symbol (Symbol): The symbol object containing multipliers and other details.
        **kwargs: Additional arguments to initialize the position.

    Returns:
        Position: An instance of `EquityPosition`, `OptionPosition`, or `FuturePosition`.

    Raises:
        ValueError: If the asset type is unsupported.
    """
    asset_classes: Dict[SecurityType, type] = {
        SecurityType.STOCK: EquityPosition,
        SecurityType.OPTION: OptionPosition,
        SecurityType.FUTURE: FuturePosition,
    }

    if asset_type not in asset_classes:
        raise ValueError(f"Unsupported asset type: {asset_type}")

    kwargs["price_multiplier"] = symbol.price_multiplier
    kwargs["quantity_multiplier"] = symbol.quantity_multiplier

    if asset_type == SecurityType.FUTURE:
        kwargs["initial_margin"] = symbol.initial_margin

    return asset_classes[asset_type](**kwargs)

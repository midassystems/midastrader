from typing import Optional, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from midas.symbol import SecurityType, Symbol, Right


@dataclass
class Impact:
    margin_required: float
    unrealized_pnl: float
    liquidation_value: float
    cash: float


@dataclass
class Position(ABC):
    action: str  # BUY/SELL
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
        # Type check
        if not isinstance(self.action, str):
            raise TypeError("'action' field must be of type str.")
        if not isinstance(self.avg_price, (int, float)):
            raise TypeError("'avg_price' field must be of type int or float.")
        if not isinstance(self.quantity, (float, int)):
            raise TypeError("'quantity' field must be of type int or float.")
        if not isinstance(self.price_multiplier, (int, float)):
            raise TypeError(
                "'price_multiplier' field must be of type int or float."
            )
        if not isinstance(self.quantity_multiplier, int):
            raise TypeError("'quantity_multiplier' field must be of type int.")
        if not isinstance(self.market_price, (int, float)):
            raise TypeError(
                "'market_price' field must be of type int or float."
            )

        # Value constraints
        if self.action not in ["BUY", "SELL"]:
            raise ValueError("'action' field must be either ['BUY','SELL'].")
        if self.price_multiplier <= 0:
            raise ValueError(
                "'price_multiplier' field must be greater than zero."
            )
        if self.quantity_multiplier <= 0:
            raise ValueError(
                "'quantity_multiplier' field must be greater than zero."
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
        pass

    @abstractmethod
    def calculate_initial_value(self) -> None:
        pass

    @abstractmethod
    def calculate_initial_cost(self) -> None:
        pass

    @abstractmethod
    def calculate_market_value(self) -> None:
        pass

    @abstractmethod
    def calculate_unrealized_pnl(self) -> None:
        pass

    @abstractmethod
    def calculate_margin_required(self) -> None:
        pass

    @abstractmethod
    def calculate_liquidation_value(self) -> None:
        pass

    @abstractmethod
    def update(
        self, quantity: int, avg_price: float, market_price: float, action: str
    ) -> Impact:
        pass

    def to_dict(self) -> dict:
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
        return (
            f"{indent}Action: {self.action}\n"
            f"{indent}Average Price: {self.avg_price}\n"
            f"{indent}Quantity: {self.quantity}\n"
            f"{indent}Price Multiplier: {self.price_multiplier}\n"
            f"{indent}Quantity Multiplier: {self.quantity_multiplier}\n"
            f"{indent}Initial Value: {self.initial_value}\n"
            f"{indent}Initial Cost: {self.initial_cost}\n"
            f"{indent}Market Price: {self.market_price}\n"
            f"{indent}Market Value: {self.market_value}\n"
            f"{indent}Unrealized P&L: {self.unrealized_pnl}\n"
            f"{indent}Liquidation Value: {self.liquidation_value}\n"
            f"{indent}Margin Required: {self.margin_required}\n"
        )


@dataclass
class FuturePosition(Position):
    initial_margin: float  # Margin required per contract

    def __post_init__(self):
        # Type check
        if not isinstance(self.initial_margin, (int, float)):
            raise TypeError(
                "'initial_margin' field must be of type int or float."
            )

        # Value constraints
        if self.initial_margin < 0:
            raise ValueError("'initial_margin' field must be non-negative.")

        super().__post_init__()

    def position_impact(self) -> Impact:
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
        self.initial_value = (
            self.avg_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def calculate_initial_cost(self) -> None:
        self.initial_cost = self.initial_margin * abs(self.quantity)

    def calculate_market_value(self) -> None:
        self.market_value = (
            self.market_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def calculate_unrealized_pnl(self) -> None:
        self.unrealized_pnl = (
            (self.market_price - self.avg_price)
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def calculate_margin_required(self) -> None:
        self.margin_required = self.initial_margin * abs(self.quantity)

    def calculate_liquidation_value(self) -> None:
        self.liquidation_value = self.initial_cost + (
            (self.market_price - self.avg_price)
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def update(
        self, quantity: int, avg_price: float, market_price: float, action: str
    ) -> Impact:
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

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update(
            {
                "initial_margin": self.initial_margin,
            }
        )
        return base_dict

    def pretty_print(self, indent: str = "") -> str:
        string = super().pretty_print(indent)
        string += f"{indent}Initial Margin': {self.initial_margin}\n"
        return string


@dataclass
class EquityPosition(Position):
    def position_impact(self) -> Impact:
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
        self.initial_value = (
            self.avg_price * self.quantity * self.quantity_multiplier
        )

    def calculate_initial_cost(self) -> None:
        self.initial_cost = self.initial_value

    def calculate_market_value(self) -> None:
        self.market_value = (
            self.market_price * self.quantity * self.quantity_multiplier
        )

    def calculate_unrealized_pnl(self) -> None:
        self.unrealized_pnl = (
            self.market_price * self.quantity * self.quantity_multiplier
        ) - self.initial_cost

    def calculate_margin_required(self) -> None:
        self.margin_required = 0

    def calculate_liquidation_value(self) -> None:
        self.liquidation_value = (
            self.market_price * self.quantity * self.quantity_multiplier
        )

    def update(
        self, quantity: int, avg_price: float, market_price: float, action: str
    ) -> Impact:
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

    def to_dict(self):
        base_dict = super().to_dict()
        return base_dict

    def pretty_print(self, indent: str = "") -> str:
        return super().pretty_print(indent)


@dataclass
class OptionPosition(Position):
    type: Right
    strike_price: float
    expiration_date: str = ""

    def __post_init__(self):
        # Type Check
        if not isinstance(self.type, Right):
            raise TypeError("'type' field must be of type Right enum.")
        if not isinstance(self.strike_price, (int, float)):
            raise TypeError(
                "'strike_price' field must be of type int or float."
            )
        if not isinstance(self.expiration_date, str):
            raise TypeError("'expiration_date' field must be of type str.")

        # Value Constraint
        if self.strike_price <= 0:
            raise ValueError("'strike_price' field must be greater than zero.")

        super().__post_init__()

    def position_impact(self) -> Impact:
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
        self.initial_value = (
            self.avg_price
            * self.quantity_multiplier
            * self.price_multiplier
            * self.quantity
        )

    def calculate_initial_cost(self) -> None:
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
        self.market_value = (
            self.market_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def calculate_unrealized_pnl(self) -> None:
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
        self.margin_required = 0

    def calculate_liquidation_value(self) -> None:
        self.liquidation_value = (
            self.market_price
            * self.price_multiplier
            * self.quantity
            * self.quantity_multiplier
        )

    def update(self, quantity: int, price: float, action: str) -> Impact:
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

    def to_dict(self):
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
        string = super().pretty_print(indent)
        string += f"{indent}Strike Price: {self.strike_price}\n"
        string += f"{indent}Expiration date: {self.expiration_date}\n"
        string += f"{indent}Type: {self.type.value}\n"
        return string


def position_factory(
    asset_type: SecurityType, symbol: Symbol, **kwargs
) -> Position:
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

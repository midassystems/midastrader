# MidasTrader

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![pypi-version](https://img.shields.io/pypi/v/midastrader.svg)](https://pypi.org/project/midastrader/)

MidasTrader is a robust trading system designed for seamless transitions between backtesting and live trading without requiring changes to user code. It integrates a flexible architecture combining a data engine, execution engine, and core components that streamline the strategy development process. The system is built with a multi-threaded design where each component communicates via a shared message bus.

### Key Components

1. **Core Engine**:

   - Central to the system, the Core Engine includes:
     - **Order Book**: Tracks market depth and price movements.
     - **Portfolio Server**: Manages and tracks portfolio allocations and positions.
     - **Performance Tracking**: Calculates and monitors key trading metrics.
     - **Order Management System**: Handles order placement, modifications, and cancellations.
     - **Base Strategy**: A foundation for user-defined strategies.

2. **Data Engine**:

   - Connects to user-defined data sources:
     - **Midas Server**: Access historical data via the Midas ecosystem.
     - **Binary Data Files**: Handles local files encoded with the Midas Binary Encoding Library.
     - **External Sources**: Currently supports Databento, with more integrations planned.

3. **Execution Engine**:

   - Facilitates live trading by connecting to brokers:
     - Currently supports Interactive Brokers.
     - Users can configure broker details in the `config.toml` file.

## Installation

You can install `midastrader` directly from [PyPI](https://pypi.org/project/midastrader/):

```bash
pip install midastrader
```

## Configuration

### Configuration File (`config.toml`)

Define system parameters, including data sources, execution settings, and strategy configuration.

- Example : [config.toml](example/config.toml)

### Strategy File (`logic.py`)

Strategies are implemented by extending the `BaseStrategy` class. Define your custom logic in Python.

- Example : [logic.py](example/logic.py)

## Usage

#### CLI Mode

Run the system using the following commands:

```bash
# Backtest Mode
midas path/to/config.toml backtest

# Live Mode
midas path/to/config.toml live
```

#### Application Mode

Alternatively, you can use the system programmatically in your application:

```python
from midas.cli import run

# Backtest Mode
run("path/to/config.toml", "backtest")

# Live Mode
run("path/to/config.toml", "live")
```

## Supported Features

<!-- | ✅  | Alpha Vantage           | -->
<!-- | ❌  | Yahoo Finance (Planned) | -->
<!-- | ❌  | Quandl (Planned)        | -->

|     | **Data Vendors** |
| --- | ---------------- |
| ✅  | Databento        |

|     | **Brokers**         |
| --- | ------------------- |
| ✅  | Interactive Brokers |

<!-- | ✅  | TD Ameritrade       | -->
<!-- | ❌  | E\*TRADE            | -->
<!-- | ❌  | Robinhood           | -->

## Future Plans

- Add more data sources.
- Integrate additional brokers.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request with suggestions or improvements.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

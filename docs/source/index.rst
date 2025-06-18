MidasTrader
===========

MidasTrader is a robust trading system designed for seamless transitions between backtesting and live trading without requiring changes to user code.

.. admonition:: Note
   :class: important

   These documentation pages are under active development and will be updated frequently 
   as the project evolves. Some information may change often until the system reaches a stable state.


Key Components
--------------

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


.. Getting Started
.. -----------
..
.. :doc:`usage` 
..

Resources
--------

.. toctree::
   :maxdepth: 1
  
   usage
   .. config
   .. design
   api
   .. faq

Links
---------------------

- 📖 GitHub: https://github.com/midassystems/midastrader


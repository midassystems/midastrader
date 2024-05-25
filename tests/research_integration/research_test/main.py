
import logging
import numpy as np
import pandas as pd
from decouple import config

from .logic import Cointegrationzscore
from midas.client import DatabaseClient
from midas.research.data import DataProcessing
from midas.research.backtester import VectorizedBacktest

from quantAnalytics.returns import Returns
from quantAnalytics.risk import RiskAnalysis
from quantAnalytics.report import ReportGenerator
from quantAnalytics.visualization import Visualizations
from quantAnalytics.regression import RegressionAnalysis
from quantAnalytics.performance import PerformanceStatistics


database = DatabaseClient(config('MIDAS_API_KEY'), config('MIDAS_URL'))

def main():
    # Set-up Report
    report_path = "/Users/anthony/trading/strategies/cointegrationzscore/research/outputs/cointegrationzscore.html"
    custom_css = "/Users/anthony/trading/strategies/cointegrationzscore/research/styles.css"
    report = ReportGenerator(report_path, custom_css)

    # Step 1 : Set-Up
    # Parameters
    start_date="2023-01-01T12:00:00"
    end_date="2024-05-07T12:00:00"

    contract_details = {'HE.n.0': {'quantity_multiplier': 40000, 'price_multiplier': 0.01}, 'ZC.n.0':{'quantity_multiplier': 5000, 'price_multiplier': 0.01}}
    tickers = list(contract_details.keys())
    benchmark=["^GSPC"]
    entry = [2.0]
    exit = [1.0]

    # Strategy
    strategy = Cointegrationzscore(tickers, report)

    # Step 2 : Retrieve Data
    # Strategy Data
    data_processing = DataProcessing(database)
    data_processing.get_data(tickers, start_date,end_date, "drop")
    data = data_processing.processed_data
    data=data.pivot(index='timestamp', columns='symbol', values='close')
    data.dropna(inplace=True)

    # Benchmark Data
    benchmark_data = database.get_bar_data(benchmark, start_date, end_date)
    benchmark_df = pd.DataFrame(benchmark_data)
    benchmark_df['close'] = benchmark_df['close'].astype(float)

    # Step 3 : Run Backtest
    backtest = VectorizedBacktest(strategy, data, contract_details, initial_capital=10000)
    backtest.setup()
    backtest_results, backtest_summary_stats = backtest.run_backtest(position_lag=1)
    stats_df = pd.DataFrame.from_dict(backtest_summary_stats, orient='index', columns=['Value'])

    # Step 4 : Add performance components to report
    tab = "    "
    report.add_text("<section class='performance'>")
    report.add_text(f"{tab}<h3>Performance Metrics</h3>")
    report.add_dataframe(stats_df, title="Summary Stats")
    report.add_image(Visualizations.line_plot, indent = 1, y = backtest_results['equity_value'], x = pd.to_datetime(backtest_results.index, unit='ns'), title = "Equity Curve", x_label="Time", y_label="Equity Value")
    report.add_image(Visualizations.line_plot, indent = 1, y = backtest_results['cumulative_return'], x = pd.to_datetime(backtest_results.index, unit='ns'),title = "Cumulative Return", x_label="Time", y_label = "Return Value")
    report.add_image(Visualizations.line_plot, indent = 1, y = backtest_results['drawdown'].tolist(), x = pd.to_datetime(backtest_results.index, unit='ns'), title = "Drawdown Curve", x_label="Time", y_label="Drawdown Value")
    report.add_text("</section>")
    
    # Step 6 : Format Backtest Results
    columns_of_interest = ['equity_value']
    strategy_equity_df = backtest_results[columns_of_interest].copy()
    strategy_equity_df.reset_index(inplace=True)

    ## Regression Analysis
    # Step 7 : Preprocessing
    regression_analysis = RegressionAnalysis(strategy_equity_df, benchmark_df)

    # Step 8 : Perform Regression and Validate model
    regression_results = regression_analysis.perform_regression_analysis()
    validation_results = regression_analysis.validate_model()

    # Step 9 : Alpha/Beta Analysis
    alpha_analysis = regression_analysis.analyze_alpha()
    beta_analysis = regression_analysis.analyze_beta()

    # Step 10 :  Calculate Returns 
    strategy_returns = Returns.simple_returns(np.array(strategy_equity_df['equity_value']))

    # Step 10 : Measure risk deviations
    volatility_thresholds = RiskAnalysis.calculate_volatility_and_zscore_annualized(strategy_returns)

    # Step 11 : Performance Attribution
    performance_attribution = regression_analysis.performance_attribution()

    # Step 12 : Risk Decomposition
    volatility_decomposition = regression_analysis.risk_decomposition()

    # Step : Sharpe Ratio
    sharpe_ratio_results = RiskAnalysis.sharpe_ratio(strategy_returns)

    # Step 13 : Hedge Analysis
    hedge_analysis = regression_analysis.hedge_analysis()

    # Step 14 : Combine regression summary statistics
    combined_data = {**performance_attribution, **volatility_decomposition, 'Sharpe Ratio': sharpe_ratio_results, **hedge_analysis}
    stats_df = pd.DataFrame(list(combined_data.items()), columns=['Metric', 'Value'])

    # Step 15 : Update report with regression results
    tab = "    "
    report.add_text("<section class='regression'>")
    report.add_text(f"{tab}<h3>Regression Analysis</h3>")
    report.add_text(regression_results.as_html())
    report.add_text(RegressionAnalysis.display_regression_validation_results(validation_results, False, True, indent = 1))
    report.add_text(RegressionAnalysis.display_alpha_analysis_results(alpha_analysis, False, True, indent = 1))
    report.add_text(RegressionAnalysis.display_beta_analysis_results(beta_analysis, False, True, indent = 1))
    report.add_text(RiskAnalysis.display_volatility_zscore_results(volatility_thresholds, False, True, indent = 1))
    report.add_dataframe(stats_df, title="Summary Stats")
    report.add_text("</section>")

    # Step 16 : Complete Report
    report.complete_report()
    print("Report generated.")

if __name__ == "__main__":
    main()


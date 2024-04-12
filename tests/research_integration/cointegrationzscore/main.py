
import logging
from decouple import config
import pandas as pd

from .logic import Cointegrationzscore
from client import DatabaseClient

from research.data import DataProcessing
from research.report import HTMLReportGenerator
from research.backtester import VectorizedBacktest
from research.analysis import RegressionAnalysis
from research.backtester import PerformanceStatistics

logging.basicConfig(level=logging.INFO)

database  = DatabaseClient(config('MIDAS_API_KEY'), config('MIDAS_URL'))

if __name__ == "__main__":
    # Set-up Report
    report_path = "/Users/anthony/git-projects/midas/midasPython/tests/research_integration/cointegrationzscore/outputs/cointegrationzscore.html"
    report = HTMLReportGenerator(report_path)

    # Step 1 : Set-Up
    # Parameters
    start_date = "2024-01-06"
    end_date = "2024-02-07"
    tickers = ['HE.n.0', 'ZC.n.0']
    benchmark=["^GSPC"]
    entry = [0.0]
    exit = [2.0]

    # Strategy
    strategy = Cointegrationzscore()

    # Step 2 : Retrieve Data
    # Strategy Data
    data_processing = DataProcessing(database)
    data_processing.get_data(tickers, start_date,end_date, "drop")
    data = data_processing.processed_data

    data.dropna(inplace=True)

    # Benchmark Data
    benchmark_data = database.get_benchmark_data(benchmark, start_date, end_date)
    benchmark_df = pd.DataFrame(benchmark_data)
    benchmark_df['timestamp'] = pd.to_datetime(benchmark_df['timestamp'])
    benchmark_df['close'] = benchmark_df['close'].astype(float)

    # Step 3 : Run Backtest
    backtest = VectorizedBacktest(data, strategy, initial_capital=10000)
    backtest_setup =  backtest.setup()
    report.add_html("Strategy Preparation")
    report.add_html(backtest_setup)

    backtest_results = backtest.run_backtest(entry_threshold=entry[0], exit_threshold=exit[0])

    tab = "    "
    report.add_html("<section class='performance'>")
    report.add_html(f"{tab}<h2>Performance Metrics</h2>")
    report.add_image(PerformanceStatistics.plot_curve, indent = 1, y = backtest_results['equity_value'], title = "Equity Curve", x_label="Time", y_label="Equity Value", show_plot=False)
    report.add_image(PerformanceStatistics.plot_curve, indent = 1, y = backtest_results['cumulative_return'], title = "Cumulative Return", x_label="Time", y_label = "Return Value", show_plot=False)
    report.add_image(PerformanceStatistics.plot_curve, indent = 1, y = backtest_results['drawdown'].tolist(), title = "Drawdown Curve", x_label="Time", y_label="Drawdown Value", show_plot=False)
    report.add_html("</section>")
    
    # Step 4 : Format Backtest Results
    columns_of_interest = ['equity_value']
    backtest_data = backtest.backtest_data
    strategy_equity_df= backtest_data[columns_of_interest].copy()
    strategy_equity_df.reset_index(inplace=True)

    ## Regression Analysis
    # Step 7 : Preprocessing
    regression_analysis = RegressionAnalysis(strategy_equity_df, benchmark_df)

    # Step 8 : Perform Regression and Validate model
    regression_results = regression_analysis.perform_regression_analysis()
    validation_results = regression_analysis.validate_model()
    print(regression_results)
    print(validation_results)

    # Step 9 : Alpha/Beta Analysis
    alpha_analysis = regression_analysis.analyze_alpha()
    beta_analysis = regression_analysis.analyze_beta()
    print(alpha_analysis)
    print(beta_analysis)

    # Step 10 : Measure risk deviations
    volatility_thresholds = regression_analysis.calculate_volatility_and_zscore_annualized()
    print(volatility_thresholds)

    # Step 11 : Performance Attribution
    performance_attribution = regression_analysis.performance_attribution()
    print(performance_attribution)

    # Step 12 : Risk Decomposition
    volatility_decomposition = regression_analysis.risk_decomposition()
    print(volatility_decomposition)

    # Step : Sharpe Ratio
    sharpe_ratio_results = regression_analysis.calculate_sharpe_ratio()
    print(sharpe_ratio_results)

    # Step 13 : Hedge Analysis
    hedge_analysis = regression_analysis.hedge_analysis()
    print(hedge_analysis)

    # Step 13 : Validate or Invalidate Strategy

    # Complete Report
    report.complete_report()




# def run_sensitivity_analysis(backtest, entry_thresholds, exit_thresholds):
#     sensitivity_results = {}
#     for entry_threshold in entry_thresholds:
#         for exit_threshold in exit_thresholds:
#             backtest_results = backtest.run_backtest(entry_threshold, exit_threshold)
#             max_drawdown = backtest_results['drawdown'].min()
#             total_return = backtest_results['cumulative_return'].iloc[-1]
#             sensitivity_results[(entry_threshold, exit_threshold)] = {"total_return": total_return, "max_drawdown": max_drawdown}
#     return sensitivity_results

# use case
# Sensitvity Anlysis
#     # Add Summary Results to Report
#     tab = "    "
#     self.report_generator.add_html("<section class='summary'>")
#     self.report_generator.add_html(f"{tab}<h2>Sensitivity Results</h2>")
#     headers = ["Entry Threshold", "Exit Threshold", "Total Return(%)", "Sharpe Ratio", "Max Drawdown"]
#     rows = [
#         [entry, exit, f"{metrics['total_return']:.2f}%", f"{0.0:.2f}", f"{metrics['max_drawdown']:.2f}%"]
#         for (entry, exit), metrics in results.items()
#     ]
#     self.report_generator.add_table(headers, rows, indent=1)
#     self.report_generator.add_html("</section>")


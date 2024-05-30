
import logging
import numpy as np
import pandas as pd
from decouple import config

from .logic import Cointegrationzscore
from midas.client import DatabaseClient
from midas.shared.utils import unix_to_iso
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
    report_path = "/Users/anthony/git-projects/midas/midasPython/tests/research_integration/research_test/outputs/cointegrationzscore.html"
    report = ReportGenerator(report_path)

    # Step 1 : Set-Up
    # Parameters
    start_date="2023-01-01T12:00:00"
    end_date="2024-05-07T12:00:00"
    contract_details = {'HE.n.0': {'quantity_multiplier': 40000, 'price_multiplier': 0.01}, 'ZC.n.0':{'quantity_multiplier': 5000, 'price_multiplier': 0.01}}
    tickers = list(contract_details.keys())
    benchmark=["^GSPC"]

    # Strategy
    strategy = Cointegrationzscore(tickers, report)

    # Step 2 : RETRIEVE DATA
    # Strategy Data
    data_processing=DataProcessing(database)
    data=data_processing.get_data(tickers, start_date,end_date, "drop")
    data=data.pivot(index='timestamp', columns='symbol', values='close')
    data.dropna(inplace=True)

    # Benchmark Data
    benchmark_data=data_processing.get_data(benchmark, start_date, end_date, "drop")
    benchmark_data=benchmark_data.pivot(index='timestamp', columns='symbol', values='close')
    data.dropna(inplace=True)

    # Benchmark Returns
    benchmark_close = pd.to_numeric(benchmark_data["^GSPC"], errors='coerce').fillna(0)
    daily_returns = Returns.simple_returns(benchmark_close.values)
    benchmark_data['period_return'] = np.insert(daily_returns, 0, 0)  # Adjust for initial zero return

    # Step 3 : RUN BACKTEST
    backtest = VectorizedBacktest(strategy, data, contract_details, initial_capital=10000)
    backtest.setup()
    backtest_results, daily_results, backtest_summary_stats = backtest.run_backtest(position_lag=1)
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

    ## Regression Analysis
    # Step 5 : Preprocessing Data
    y=pd.DataFrame(index=daily_results.index)
    y['strategy_return']=daily_results['period_return'].copy()
    y=y.drop(y.index[0])

    # Add HE and ZC simple returns as Factors
    X=pd.DataFrame(index=daily_results.index)
    X['HE_futures']=daily_results["HE.n.0"].pct_change()
    X['ZC_futures']=daily_results["ZC.n.0"].pct_change()
    X=X.drop(X.index[0])

    # Add Benchmark returns as Factor
    # X["bm_return"]=benchmark_data['period_return'].copy()
    # X["bm_return"]=benchmark_data['period_return'].copy()
    # X[''] # Add other factors (AssetsPRices)

    # Convert index to readable datetime
    # X.index=pd.to_datetime(X.index.map(lambda x: unix_to_iso(x)), utc=True)
    # X=X.resample('D').last()
    # X.dropna(inplace=True)
    
    # y.index=pd.to_datetime(y.index.map(lambda x: unix_to_iso(x)), utc=True)
    # y=y.resample('D').last()
    # y.dropna(inplace=True)

    # Align by Date
    # aligned_returns = pd.concat([y, X], axis=1, join='inner').dropna()
    # y=aligned_returns['strategy_return']
    # X=aligned_returns['bm_return']

    #  Step 6 : Fit Model
    regression_analysis = RegressionAnalysis(y, X)
    summary = regression_analysis.fit()
    
    # step 7 : Evaluate Model
    regression_results = regression_analysis.evaluate()

    # Step 8 : Risk Decomposition
    strategy_return= np.array(daily_results['period_return'])
    volatility_thresholds = RiskAnalysis.calculate_volatility_and_zscore_annualized(strategy_return)
    volatility_decomposition = regression_analysis.risk_decomposition()

    # Step 9 : Performance Attribution
    performance_attribution = regression_analysis.performance_attribution()

    # # Step 13 : Hedge Analysis
    # hedge_analysis = regression_analysis.hedge_analysis()

    # # Step 14 : Combine regression summary statistics
    combined_data = {**performance_attribution, **volatility_decomposition}# **hedge_analysis}
    stats_df = pd.DataFrame(list(combined_data.items()), columns=['Metric', 'Value'])

    # Step 15 : Update report with regression results
    tab = "    "
    report.add_text("<section class='regression'>")
    report.add_text(f"{tab}<h3>Regression Analysis</h3>")
    report.add_text(summary.as_html())
    report.add_text(regression_results.to_html())
    report.add_dataframe(stats_df, title="Summary Stats")
    report.add_text(RiskAnalysis.display_volatility_zscore_results(volatility_thresholds, False, True, indent = 1))
    report.add_image(regression_analysis.plot_residuals, indent = 1)
    report.add_image(regression_analysis.plot_qq, indent = 1)
    report.add_image(regression_analysis.plot_influence_measures, indent = 1)
    report.add_text("</section>")

    # Step 16 : Complete Report
    report.complete_report()
    print("Report generated.")

if __name__ == "__main__":
    main()


import unittest
import numpy as np
import pandas as pd
from decimal import Decimal
from contextlib import ExitStack
from unittest.mock import MagicMock, patch
from midas.performance.regression import RegressionAnalysis

class RegressionAnalysisTests(unittest.TestCase):
    def setUp(self):
        # Sample strategy and benchmark data
        self.strategy_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            'equity_value': [100, 102, 104, 103, 105]
        })
        
        self.benchmark_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            'close': [50, 51, 52, 51, 53]
        })

        self.mock_model = MagicMock()
        self.mock_model.rsquared = 0.90
        self.mock_model.pvalues = pd.Series({
                                            "const": 0.03,
                                            "close": 0.08
                                            })
        self.mock_model.params = pd.Series({
                                            "const": 0.04,
                                            "close": 0.076941
                                            })
        self.mock_model.resid = pd.Series([0.004835, 0.004659, -0.003153, -0.006341],index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]))
        self.mock_model.conf_int.return_value = pd.DataFrame({
            0: {"const": -0.013994, "close": -0.147663},
            1: {"const": 0.022272, "close": 1.250262}
        })
        self.analysis = RegressionAnalysis(self.strategy_data.copy(), self.benchmark_data.copy())
        self.analysis.model = self.mock_model
    # Basic Validation 
    def test_standardize_to_daily_values(self):
        expected_returns = [0.0200, 0.0196078431372549, -0.009615384615384616, 0.019417475728155338]  

        # Test
        daily_returns = self.analysis._standardize_to_daily_values(self.strategy_data, 'equity_curve')
        calculated_returns_list = daily_returns.to_list()
        
        # Validation
        for i in range(0, len(expected_returns) -1):
            self.assertAlmostEqual(calculated_returns_list[i], expected_returns[i], places=4)

    def test_standardize_to_daily_values(self):
        expected_returns = [0.0200, 0.0196078431372549, -0.009615384615384616, 0.019417475728155338]  

        # Test
        daily_returns = self.analysis._standardize_to_daily_values(self.strategy_data, 'equity_value')
        calculated_returns_list = daily_returns.to_list()
        
        # Validation
        for i in range(0, len(expected_returns) -1):
            self.assertAlmostEqual(calculated_returns_list[i], expected_returns[i], places=4)

    def test_prepare_and_align_data(self):
        # Expected 
        expected_strategy_returns = [0.0200, 0.0196078431372549, -0.009615384615384616, 0.019417475728155338] 
        expected_bm_returns = [0.02, 0.0196078431372549, -0.019230769230769232, 0.0392156862745098]
 

        # Test
        strategy_returns, benchmark_returns = self.analysis._prepare_and_align_data(self.strategy_data, self.benchmark_data)
        
        # Validation
        benchmark_returns = benchmark_returns.to_list()
        strategy_returns = strategy_returns.to_list()
        self.assertEqual(len(strategy_returns), len(benchmark_returns))

        for i in range(0, len(expected_strategy_returns) -1):
            self.assertAlmostEqual(strategy_returns[i], expected_strategy_returns[i], places=4)

        for i in range(0, len(expected_bm_returns) -1):
            self.assertAlmostEqual(benchmark_returns[i], expected_bm_returns[i], places=4)

    def test_perform_regression_analysis(self):
        # Test
        self.analysis.perform_regression_analysis()
        
        # validation
        result_model = self.analysis.model
        self.assertIsNotNone(result_model, "Regression model is not fitted.")
        self.assertTrue(hasattr(result_model, 'params'), "Model has no parameters.")

    def test_validate_model_success_scenario(self):
        # Mock the model with predetermined R-squared and p-values indicating a successful validation scenario
        mock_model = MagicMock()
        mock_model.rsquared = 0.03
        mock_model.pvalues = pd.Series([0.01, 0.001])  # Assuming intercept and slope p-values
        
        # Assign the mock model to the analysis instance
        self.analysis.model = mock_model
        
        # Validate the model
        validation_results = self.analysis.validate_model()
        
        # Assert validations are as expected for a successful scenario
        self.assertTrue(validation_results['Validation Checks']['Model is valid'])
        self.assertTrue(validation_results['Validation Checks']['R-squared above threshold'])
        self.assertTrue(validation_results['Validation Checks']['P-values significant'])

    def test_validate_model_failure_scenario(self):
        # Mock the model with predetermined R-squared and p-values indicating a failure validation scenario
        mock_model = MagicMock()
        mock_model.rsquared = 0.01  # Below threshold
        mock_model.pvalues = pd.Series([0.01, 0.1])  # Assuming intercept p-value is fine but slope p-value is not significant
        
        # Assign the mock model to the analysis instance
        self.analysis.model = mock_model
        
        # Validate the model
        validation_results = self.analysis.validate_model()
        
        # Assert validations are as expected for a failure scenario
        self.assertFalse(validation_results['Validation Checks']['Model is valid'])
        self.assertFalse(validation_results['Validation Checks']['R-squared above threshold'])
        self.assertFalse(validation_results['Validation Checks']['P-values significant'])

    def test_beta(self):
        # Assuming a regression model has already been fitted in setup
        expected_beta = self.mock_model.params[1]  # Mock expected beta value
        calculated_beta = self.analysis.beta()
        self.assertAlmostEqual(calculated_beta, expected_beta, places=4)

    def test_alpha(self):
        # Expected alpha calculation
        annualized_strategy_return = np.mean(self.analysis.strategy_returns) * 252
        annualized_benchmark_return = np.mean(self.analysis.benchmark_returns) * 252
        expected_alpha = annualized_strategy_return - (self.analysis.risk_free_rate +  self.mock_model.params[1] * (annualized_benchmark_return - self.analysis.risk_free_rate))

        # Calculated alpha from the method
        calculated_alpha = self.analysis.alpha()

        self.assertAlmostEqual(calculated_alpha, expected_alpha, places=3, msg="Calculated alpha does not match expected alpha.")

    def test_analyze_alpha(self):
        alpha_results = self.analysis.analyze_alpha()

        self.assertEqual(alpha_results["Alpha (Intercept)"], 0.04)
        self.assertEqual(alpha_results["P-value"], 0.03)
        self.assertTrue(alpha_results['Alpha is significant'])
        self.assertTrue(alpha_results['Confidence Interval spans zero'])

    def test_analyze_beta(self):
        beta_results = self.analysis.analyze_beta()

        self.assertEqual(beta_results["Beta (Slope)"], 0.076941)
        self.assertEqual(beta_results["P-value"], 0.08)
        self.assertFalse(beta_results['Beta is significant'])

    def test_calculate_volatility_and_zscore(self):
        volatility_results = self.analysis.calculate_volatility_and_zscore_annualized()
        z_score_dict  = volatility_results["Z-Scores (Annualized)"]
        
        # Annualizing the daily volatility and mean return
        annualized_volatility = self.analysis.strategy_returns.std() * np.sqrt(252)
        annualized_mean_return = self.analysis.strategy_returns.mean() * 252

        self.assertEqual(volatility_results['Annualized Volatility'], annualized_volatility)
        self.assertEqual(volatility_results["Annualized Mean Return"], annualized_mean_return)
        self.assertGreater(z_score_dict['Z-score for 1 SD move (annualized)'], 0)
        self.assertGreater(z_score_dict['Z-score for 2 SD move (annualized)'], 0)
        self.assertGreater(z_score_dict['Z-score for 3 SD move (annualized)'], 0)

    def test_risk_decomposition(self):
        risk_results = self.analysis.risk_decomposition()

        self.assertGreater(risk_results['Market Volatility'], 0)
        self.assertGreater(risk_results['Idiosyncratic Volatility'], 0)
        self.assertGreater(risk_results['Total Volatility'], 0)

    def test_performance_attribution(self):
        perf_results = self.analysis.performance_attribution()

        self.assertNotEqual(perf_results['Market Contribution'], 0)
        self.assertNotEqual(perf_results['Idiosyncratic Contribution'], 0)
        self.assertNotEqual(perf_results['Total Contribution'], 0)

    def test_calculate_sharpe_ratio(self):
        risk_free_rate = 0.01
        sharpe_ratio_results = self.analysis.calculate_sharpe_ratio(risk_free_rate)

        # Basic checks for expected keys
        self.assertIn("sharpe_ratio", sharpe_ratio_results)
        self.assertIn("annualized_return", sharpe_ratio_results)
        self.assertIn("annualized_volatility", sharpe_ratio_results)
        self.assertIn("risk_free_rate", sharpe_ratio_results)

        # Check if Sharpe Ratio calculation makes sense
        self.assertEqual(sharpe_ratio_results["risk_free_rate"], risk_free_rate)

    def test_hedge_analysis(self):
        hedge_results = self.analysis.hedge_analysis()

        # Basic checks for expected keys
        self.assertGreater(hedge_results["Portfolio Dollar Beta"], 0)
        self.assertGreater(hedge_results["Beta"], 0)

        self.assertIn("Market Hedge NMV", hedge_results)
    
    def test_compile_reults(self):
        sharpe_ratio_return = {
            "sharpe_ratio": Decimal('1.5'),
            "annualized_return": Decimal('0.1'),
            "annualized_volatility": Decimal('0.2'),
            "risk_free_rate": Decimal(0.01)
        }
        performance_attribution_return_value = {
            "Market Contribution": Decimal('0.08'),
            "Idiosyncratic Contribution": Decimal('0.04'),
            "Total Contribution": Decimal('0.12')
        }
        risk_decomposition_return_value = {
            "Market Volatility": Decimal('0.15'),
            "Idiosyncratic Volatility": Decimal('0.05'),
            "Total Volatility": Decimal('0.16')
        }
        hedge_analysis_return_value = {
            "Portfolio Dollar Beta": Decimal('10000'),
            "Market Hedge NMV": Decimal('-10000')
        }

        with ExitStack() as stack:
            mock_sharpe = stack.enter_context(patch.object(self.analysis, 'calculate_sharpe_ratio', return_value=sharpe_ratio_return))
            mock_risk_decomp = stack.enter_context(patch.object(self.analysis, 'performance_attribution', return_value=performance_attribution_return_value))
            mock_per_attrb = stack.enter_context(patch.object(self.analysis, 'risk_decomposition', return_value=risk_decomposition_return_value))
            mock_hedge_analysis = stack.enter_context(patch.object(self.analysis, 'hedge_analysis', return_value=hedge_analysis_return_value))

            # Test
            results = self.analysis.compile_results()

            # expected
            annualized_strategy_return = np.mean(self.analysis.strategy_returns) * 252
            annualized_benchmark_return = np.mean(self.analysis.benchmark_returns) * 252
            expected_alpha = annualized_strategy_return - (self.analysis.risk_free_rate +  self.mock_model.params[1] * (annualized_benchmark_return - self.analysis.risk_free_rate))


            # Validation
            expected_keys = ["r_squared", "p_value_alpha", "p_value_beta", "risk_free_rate", "alpha", "beta", "sharpe_ratio", 
                            "annualized_return", "market_contribution", "idiosyncratic_contribution", 
                            "total_contribution", "annualized_volatility", "market_volatility", 
                            "idiosyncratic_volatility", "total_volatility", "portfolio_dollar_beta", "market_hedge_nmv"]

            for key in expected_keys:
                self.assertIn(key, results)
                self.assertIsInstance(results[key], str)

            # Example of asserting a specific value
            self.assertAlmostEqual(results["r_squared"], str(self.mock_model.rsquared), places=2)
            self.assertAlmostEqual(results["p_value_alpha"], str(self.mock_model.pvalues['const']), places=2)
            self.assertAlmostEqual(results["p_value_beta"], str(self.mock_model.pvalues[1]), places=2)
            self.assertEqual(results["risk_free_rate"], str('0.01'))  # Assuming this was set in the RegressionAnalysis initialization
            self.assertAlmostEqual(float(results["alpha"]), expected_alpha, places=2)
            self.assertAlmostEqual(float(results["beta"]), self.mock_model.params[1], places=2)
            self.assertEqual(float(results["sharpe_ratio"]), 1.5)
            self.assertEqual(float(results["annualized_return"]), 0.1)
            self.assertEqual(float(results["market_contribution"]), 0.08)
            self.assertEqual(float(results["idiosyncratic_contribution"]), 0.04)
            self.assertEqual(float(results["total_contribution"]), 0.12)
            self.assertEqual(float(results["annualized_volatility"]), 0.2)
            self.assertEqual(float(results["market_volatility"]), 0.15)
            self.assertEqual(float(results["idiosyncratic_volatility"]), 0.05)
            self.assertEqual(float(results["total_volatility"]), 0.16)
            self.assertEqual(float(results["portfolio_dollar_beta"]), 10000)
            self.assertEqual(float(results["market_hedge_nmv"]), -10000)

if __name__ == '__main__':
    unittest.main()

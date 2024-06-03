import unittest
from unittest.mock import Mock, patch

from midas.shared.regression import RegressionResults

# #TODO: edge cases
class TestRegressionResults(unittest.TestCase):    
    def setUp(self) -> None:
        self.regression_results = RegressionResults(
            backtest=1,
            risk_free_rate=0.02,
            r_squared=0.95,
            adj_r_squared=0.94,
            RMSE=0.01,
            MAE=0.02,
            f_statistic=50.0,
            f_statistic_p_value=0.0001,
            durbin_watson=2.0,
            jarque_bera=5.0,
            jarque_bera_p_value=0.05,
            condition_number=10.0,
            vif={'beta1': 1.5, 'beta2': 2.0},
            alpha=0.05,
            p_value_alpha=0.01,
            beta={'beta1': 1.2, 'beta2': 0.8},
            p_value_beta={'beta1': 0.05, 'beta2': 0.01},
            total_contribution=0.5,
            systematic_contribution=0.3,
            idiosyncratic_contribution=0.2,
            total_volatility=0.15,
            systematic_volatility=0.1,
            idiosyncratic_volatility=0.05,
            timeseries_data=[
                {'timestamp': 1706850000000000000, 'daily_benchmark_return': 0.0}, 
                {'timestamp': 1707109200000000000, 'daily_benchmark_return': 0.0024}, 
                {'timestamp': 1707195600000000000, 'daily_benchmark_return': 0.0063}, 
                {'timestamp': 1707282000000000000, 'daily_benchmark_return': 0.0056}, 
                {'timestamp': 1707368400000000000, 'daily_benchmark_return': 0.0152}, 
                {'timestamp': 1707454800000000000, 'daily_benchmark_return': 0.0052}, 
                {'timestamp': 1707714000000000000, 'daily_benchmark_return': -0.0016}, 
                {'timestamp': 1707800400000000000, 'daily_benchmark_return': 0.0022}, 
                {'timestamp': 1707886800000000000, 'daily_benchmark_return': -0.0118}, 
                {'timestamp': 1707973200000000000, 'daily_benchmark_return': 0.0061}
            ]
        )

    # Basic Validation
    def test_to_dict(self):
        # test
        regression_dict = self.regression_results.to_dict()

        # validate
        self.assertEqual(regression_dict['backtest'], self.regression_results.backtest)
        self.assertEqual(regression_dict['r_squared'], self.regression_results.r_squared)
        self.assertEqual(regression_dict['adjusted_r_squared'], self.regression_results.adj_r_squared)
        self.assertEqual(regression_dict['RMSE'], self.regression_results.RMSE)
        self.assertEqual(regression_dict['MAE'], self.regression_results.MAE)
        self.assertEqual(regression_dict['alpha'], self.regression_results.alpha)
        self.assertEqual(regression_dict['f_statistic'], self.regression_results.f_statistic)
        self.assertEqual(regression_dict['f_statistic_p_value'], self.regression_results.f_statistic_p_value)


    def test_type_constraints(self):
        with self.assertRaisesRegex(ValueError,"vif must be a dictionary"):
            RegressionResults(
                backtest=1,
                risk_free_rate=0.02,
                r_squared=0.95,
                adj_r_squared=0.94,
                RMSE=0.01,
                MAE=0.02,
                f_statistic=50.0,
                f_statistic_p_value=0.0001,
                durbin_watson=2.0,
                jarque_bera=5.0,
                jarque_bera_p_value=0.05,
                condition_number=10.0,
                vif="{'beta1': 1.5, 'beta2': 2.0}",
                alpha=0.05,
                p_value_alpha=0.01,
                beta={'beta1': 1.2, 'beta2': 0.8},
                p_value_beta={'beta1': 0.05, 'beta2': 0.01},
                total_contribution=0.5,
                systematic_contribution=0.3,
                idiosyncratic_contribution=0.2,
                total_volatility=0.15,
                systematic_volatility=0.1,
                idiosyncratic_volatility=0.05,            
                timeseries_data=[
                {'timestamp': 1706850000000000000, 'daily_benchmark_return': 0.0}, 
                {'timestamp': 1707109200000000000, 'daily_benchmark_return': 0.0024}, 
                {'timestamp': 1707195600000000000, 'daily_benchmark_return': 0.0063}, 
                {'timestamp': 1707282000000000000, 'daily_benchmark_return': 0.0056}, 
                {'timestamp': 1707368400000000000, 'daily_benchmark_return': 0.0152}, 
                {'timestamp': 1707454800000000000, 'daily_benchmark_return': 0.0052}, 
                {'timestamp': 1707714000000000000, 'daily_benchmark_return': -0.0016}, 
                {'timestamp': 1707800400000000000, 'daily_benchmark_return': 0.0022}, 
                {'timestamp': 1707886800000000000, 'daily_benchmark_return': -0.0118}, 
                {'timestamp': 1707973200000000000, 'daily_benchmark_return': 0.0061}
                ]
            )
                
        with self.assertRaisesRegex(ValueError,"beta must be a dictionary"):
            RegressionResults(
                backtest=1,
                risk_free_rate=0.02,
                r_squared=0.95,
                adj_r_squared=0.94,
                RMSE=0.01,
                MAE=0.02,
                f_statistic=50.0,
                f_statistic_p_value=0.0001,
                durbin_watson=2.0,
                jarque_bera=5.0,
                jarque_bera_p_value=0.05,
                condition_number=10.0,
                vif={'beta1': 1.5, 'beta2': 2.0},
                alpha=0.05,
                p_value_alpha=0.01,
                beta="{'beta1': 1.2, 'beta2': 0.8}",
                p_value_beta={'beta1': 0.05, 'beta2': 0.01},
                total_contribution=0.5,
                systematic_contribution=0.3,
                idiosyncratic_contribution=0.2,
                total_volatility=0.15,
                systematic_volatility=0.1,
                idiosyncratic_volatility=0.05,
                 timeseries_data=[
                {'timestamp': 1706850000000000000, 'daily_benchmark_return': 0.0}, 
                {'timestamp': 1707109200000000000, 'daily_benchmark_return': 0.0024}, 
                {'timestamp': 1707195600000000000, 'daily_benchmark_return': 0.0063}, 
                {'timestamp': 1707282000000000000, 'daily_benchmark_return': 0.0056}, 
                {'timestamp': 1707368400000000000, 'daily_benchmark_return': 0.0152}, 
                {'timestamp': 1707454800000000000, 'daily_benchmark_return': 0.0052}, 
                {'timestamp': 1707714000000000000, 'daily_benchmark_return': -0.0016}, 
                {'timestamp': 1707800400000000000, 'daily_benchmark_return': 0.0022}, 
                {'timestamp': 1707886800000000000, 'daily_benchmark_return': -0.0118}, 
                {'timestamp': 1707973200000000000, 'daily_benchmark_return': 0.0061}
            ]
            )
            
        with self.assertRaisesRegex(ValueError, "p_value_beta must be a dictionary"):
            RegressionResults(
                backtest=1,
                risk_free_rate=0.02,
                r_squared=0.95,
                adj_r_squared=0.94,
                RMSE=0.01,
                MAE=0.02,
                f_statistic=50.0,
                f_statistic_p_value=0.0001,
                durbin_watson=2.0,
                jarque_bera=5.0,
                jarque_bera_p_value=0.05,
                condition_number=10.0,
                vif={'beta1': 1.5, 'beta2': 2.0},
                alpha=0.05,
                p_value_alpha=0.01,
                beta={'beta1': 1.2, 'beta2': 0.8},
                p_value_beta="{'beta1': 0.05, 'beta2': 0.01}",
                total_contribution=0.5,
                systematic_contribution=0.3,
                idiosyncratic_contribution=0.2,
                total_volatility=0.15,
                systematic_volatility=0.1,
                idiosyncratic_volatility=0.05,
                timeseries_data=[
                    {'timestamp': 1706850000000000000, 'daily_benchmark_return': 0.0}, 
                    {'timestamp': 1707109200000000000, 'daily_benchmark_return': 0.0024}, 
                    {'timestamp': 1707195600000000000, 'daily_benchmark_return': 0.0063}, 
                    {'timestamp': 1707282000000000000, 'daily_benchmark_return': 0.0056}, 
                    {'timestamp': 1707368400000000000, 'daily_benchmark_return': 0.0152}, 
                    {'timestamp': 1707454800000000000, 'daily_benchmark_return': 0.0052}, 
                    {'timestamp': 1707714000000000000, 'daily_benchmark_return': -0.0016}, 
                    {'timestamp': 1707800400000000000, 'daily_benchmark_return': 0.0022}, 
                    {'timestamp': 1707886800000000000, 'daily_benchmark_return': -0.0118}, 
                    {'timestamp': 1707973200000000000, 'daily_benchmark_return': 0.0061}
                ]
            )

        with self.assertRaisesRegex(ValueError, "timeseries_data must be a list"):
            RegressionResults(
                backtest=1,
                risk_free_rate=0.02,
                r_squared=0.95,
                adj_r_squared=0.94,
                RMSE=0.01,
                MAE=0.02,
                f_statistic=50.0,
                f_statistic_p_value=0.0001,
                durbin_watson=2.0,
                jarque_bera=5.0,
                jarque_bera_p_value=0.05,
                condition_number=10.0,
                vif={'beta1': 1.5, 'beta2': 2.0},
                alpha=0.05,
                p_value_alpha=0.01,
                beta={'beta1': 1.2, 'beta2': 0.8},
                p_value_beta={'beta1': 0.05, 'beta2': 0.01},
                total_contribution=0.5,
                systematic_contribution=0.3,
                idiosyncratic_contribution=0.2,
                total_volatility=0.15,
                systematic_volatility=0.1,
                idiosyncratic_volatility=0.05,
                timeseries_data="test"
            )
            
        with self.assertRaises(ValueError):
            RegressionResults(
                backtest=1,
                risk_free_rate="0.02",
                r_squared=0.95,
                adj_r_squared=0.94,
                RMSE=0.01,
                MAE=0.02,
                f_statistic=50.0,
                f_statistic_p_value=0.0001,
                durbin_watson=2.0,
                jarque_bera=5.0,
                jarque_bera_p_value=0.05,
                condition_number=10.0,
                vif={'beta1': 1.5, 'beta2': 2.0},
                alpha=0.05,
                p_value_alpha=0.01,
                beta={'beta1': 1.2, 'beta2': 0.8},
                p_value_beta={'beta1': 0.05, 'beta2': 0.01},
                total_contribution=0.5,
                systematic_contribution=0.3,
                idiosyncratic_contribution=0.2,
                total_volatility=0.15,
                systematic_volatility=0.1,
                idiosyncratic_volatility=0.05,
                timeseries_data=[
                    {'timestamp': 1706850000000000000, 'daily_benchmark_return': 0.0}, 
                    {'timestamp': 1707109200000000000, 'daily_benchmark_return': 0.0024}, 
                    {'timestamp': 1707195600000000000, 'daily_benchmark_return': 0.0063}, 
                    {'timestamp': 1707282000000000000, 'daily_benchmark_return': 0.0056}, 
                    {'timestamp': 1707368400000000000, 'daily_benchmark_return': 0.0152}, 
                    {'timestamp': 1707454800000000000, 'daily_benchmark_return': 0.0052}, 
                    {'timestamp': 1707714000000000000, 'daily_benchmark_return': -0.0016}, 
                    {'timestamp': 1707800400000000000, 'daily_benchmark_return': 0.0022}, 
                    {'timestamp': 1707886800000000000, 'daily_benchmark_return': -0.0118}, 
                    {'timestamp': 1707973200000000000, 'daily_benchmark_return': 0.0061}
                ]
            )
            
        with self.assertRaisesRegex(ValueError, "backtest must be an integer"):
            RegressionResults(
                backtest="1",
                risk_free_rate=0.02,
                r_squared=0.95,
                adj_r_squared=0.94,
                RMSE=0.01,
                MAE=0.02,
                f_statistic=50.0,
                f_statistic_p_value=0.0001,
                durbin_watson=2.0,
                jarque_bera=5.0,
                jarque_bera_p_value=0.05,
                condition_number=10.0,
                vif={'beta1': 1.5, 'beta2': 2.0},
                alpha=0.05,
                p_value_alpha=0.01,
                beta={'beta1': 1.2, 'beta2': 0.8},
                p_value_beta={'beta1': 0.05, 'beta2': 0.01},
                total_contribution=0.5,
                systematic_contribution=0.3,
                idiosyncratic_contribution=0.2,
                total_volatility=0.15,
                systematic_volatility=0.1,
                idiosyncratic_volatility=0.05,
                timeseries_data=[
                    {'timestamp': 1706850000000000000, 'daily_benchmark_return': 0.0}, 
                    {'timestamp': 1707109200000000000, 'daily_benchmark_return': 0.0024}, 
                    {'timestamp': 1707195600000000000, 'daily_benchmark_return': 0.0063}, 
                    {'timestamp': 1707282000000000000, 'daily_benchmark_return': 0.0056}, 
                    {'timestamp': 1707368400000000000, 'daily_benchmark_return': 0.0152}, 
                    {'timestamp': 1707454800000000000, 'daily_benchmark_return': 0.0052}, 
                    {'timestamp': 1707714000000000000, 'daily_benchmark_return': -0.0016}, 
                    {'timestamp': 1707800400000000000, 'daily_benchmark_return': 0.0022}, 
                    {'timestamp': 1707886800000000000, 'daily_benchmark_return': -0.0118}, 
                    {'timestamp': 1707973200000000000, 'daily_benchmark_return': 0.0061}
                ]
            )

if __name__ == "__main__":
    unittest.main()


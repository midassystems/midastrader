import unittest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from sklearn.linear_model import LinearRegression

from research.analysis import TimeseriesTests


def generate_residuals(autocorr_type='none', size=100):
    """
    Helper function to generate simulated residuals with specific autocorrelation properties.
    """
    np.random.seed(42)  # For reproducibility
    if autocorr_type == 'positive':
        # Generate positively autocorrelated residuals
        residuals = [np.random.randn()]
        for _ in range(1, size):
            residuals.append(residuals[-1] * 0.9 + np.random.randn())
    elif autocorr_type == 'negative':
        # Alternate signs for negative autocorrelation
        residuals = [(-1)**i * abs(np.random.randn()) for i in range(size)]
    else:
        # Generate random residuals (no autocorrelation)
        residuals = np.random.randn(size)
    return pd.DataFrame(residuals, columns=['Residuals'])

def generate_causal_data():
    np.random.seed(42)
    x = np.random.randn(100)
    # Increase the coefficient to make the causality stronger
    y = x + np.random.normal(scale=5, size=100)  # Increased noise
    data = pd.DataFrame({'x': x, 'y': y})
    return data

def generate_mean_reverting_series_known_half_life(half_life: float, size: int = 1000):
    """
    Generate a synthetic mean-reverting time series based on an AR(1) process where
    the half-life of mean reversion is known.

    Parameters:
    half_life (float): The half-life of the mean-reverting series.
    size (int): The size of the time series to generate.

    Returns:
    pd.Series: Generated mean-reverting time series.
    """
    # Calculate the phi coefficient from the half-life
    phi = np.exp(-np.log(2) / half_life)
    
    # Generate AR(1) series
    series = [np.random.normal()]
    for _ in range(1, size):
        series.append(phi * series[-1] + np.random.normal())

    return pd.Series(series)

def generate_seasonal_stationary_series(length=1000, seasonal_periods=12):
    """Generate a seasonal stationary series with a specified length and seasonality."""
    np.random.seed(42)
    # Generate a seasonal pattern
    seasonal_component = np.sin(np.linspace(0, 2 * np.pi, seasonal_periods))
    # Repeat the pattern but ensure the final series length matches the desired length
    repeats = length // seasonal_periods + 1  # Ensure enough repeats
    series = np.tile(seasonal_component, repeats)[:length]  # Trim to exact length
    noise = np.random.normal(0, 0.5, length)
    return pd.Series(series + noise)  # No need to slice noise as it's already correct length

def generate_seasonal_non_stationary_series(length=1000, start=0, slope=1):
    """Generate a non-stationary series with a specified length."""
    np.random.seed(42)
    # Create an array of increasing values based on the specified slope
    series = np.arange(start, length * slope + start, slope)
    return pd.Series(series)

def generate_cointegrated_series(n=100):
    """
    Generate a set of cointegrated time series for testing.
    """
    np.random.seed(42)
    # Generate a random walk series
    x0 = np.random.normal(0, 1, n).cumsum()
    # Generate another series which is a linear combination of x0 plus some noise
    x1 = x0 + np.random.normal(0, 1, n)
    return pd.DataFrame({'x0': x0, 'x1': x1})

def generate_non_cointegrated_series(n=100):
    """
    Generate a set of non-cointegrated time series for testing.
    """
    np.random.seed(42)
    # Generate two independent random walk series
    x0 = np.random.normal(0, 1, n).cumsum()
    x1 = np.random.normal(0, 1, n).cumsum()
    return pd.DataFrame({'x0': x0, 'x1': x1})

def generate_random_time_series(length=100, lag=2):
    """
    Generate a simple time series dataset with a known lagged relationship for testing,
    where the first 'lag' values of the lagged series are filled with random numbers.
    
    Parameters:
    - length (int): Length of the time series.
    - lag (int): The lag introduced between x0 and x1 to establish a known relationship.
    
    Returns:
    - pd.DataFrame: A DataFrame containing the time series with a known lagged relationship.
    """
    np.random.seed(42)  # Ensure reproducibility

    # Generate the base series x0
    x0 = np.random.normal(0, 1, length).cumsum()

    # Initialize x1 with the same size as x0
    x1 = np.zeros(length)

    # Fill the first 'lag' elements of x1 with random noise
    x1[:lag] = np.random.normal(0, 1, lag)

    # Fill in the rest of x1 with values from x0 lagged by 'lag' steps
    # Here, adding some noise to maintain a similar variability in x1 as in x0
    x1[lag:] = x0[:-lag] + np.random.normal(0, 0.1, length-lag)  # Adjust noise level as needed

    data = pd.DataFrame({'x0': x0, 'x1': x1})
    return data

class TestTimeseriesTests(unittest.TestCase):
    def setUp(self):
        # Create sample time series data
        np.random.seed(0)
        self.sample_series = pd.Series(np.random.randn(100))
        self.sample_dataframe = pd.DataFrame({
            'series1': np.random.randn(100),
            'series2': np.random.randn(100)
        })

        self.mean_reverting_series = TimeseriesTests.generate_mean_reverting_series()
        self.trending_series = TimeseriesTests.generate_trending_series()
        self.random_walk_series = TimeseriesTests.generate_random_walk_series(n=2000, start_value=0, step_std=1)

    # Basic Validation
    # def test_generate_mean_reverting_series_basic(self):
    #     n = 2000
    #     mu = 0
    #     theta = 0.1  # Adjust if needed
    #     sigma = 0.2  # Adjust if needed
    #     series = TimeseriesTests.generate_mean_reverting_series(n=n, mu=mu, theta=theta, sigma=sigma, start_value=1)
    #     self.assertEqual(len(series), n)
    #     self.assertEqual(series[0], 1)
    #     self.assertTrue(isinstance(series, np.ndarray))
        
    #     series_mean = np.mean(series)
    #     self.assertTrue(np.abs(series_mean - mu) < 0.05) # threshold for difference between actual mean and long-term mean

    # def test_generate_trending_series_basic(self):
    #     n = 2000
    #     series = TimeseriesTests.generate_trending_series(n=2000, start_value=0, trend=0.1, step_std=1)
    #     self.assertEqual(len(series), 2000)
    #     self.assertEqual(series[0], 0)
    #     self.assertTrue(isinstance(series, np.ndarray))

    #     # Perform linear regression
    #     X = np.arange(len(series)).reshape(-1, 1)  # Time steps as independent variable
    #     y = series  # Series values as dependent variable
    #     slope, intercept, r_value, p_value, std_err = stats.linregress(X.ravel(), y)

    #     # Verify the trend direction and significance
    #     self.assertGreater(slope, 0)  # Check if slope is significantly greater than 0
    #     self.assertLess(p_value, 0.05)  # Check if the slope is statistically significant

    # def test_generate_random_walk_series_basic(self):
    #     n=2000
    #     series = TimeseriesTests.generate_random_walk_series(n=n, start_value=0, step_std=1)
    #     self.assertEqual(len(series), n)
    #     self.assertEqual(series[0], 0)
    #     self.assertTrue(isinstance(series, np.ndarray))

    #     # Test for no clear trend using Augmented Dickey-Fuller
    #     adf_result = adfuller(series)
    #     self.assertTrue(adf_result[1] > 0.05)  # P-value should be low to reject null hypothesis of a unit root

    #     # Test for independence using autocorrelation at lag 1
    #     autocorrelation = pd.Series(series).autocorr(lag=1)

    #     # Expect autocorrelation for a random walk to be significant but not perfect
    #     self.assertTrue(0.9 < autocorrelation <= 1)

    # def test_split_data_default_ratio(self):
    #     train, test = TimeseriesTests.split_data(self.sample_dataframe)
    #     # Default split ratio is 0.8
    #     expected_train_length = int(len(self.sample_dataframe) * 0.8)
    #     expected_test_length = len(self.sample_dataframe) - expected_train_length
    #     self.assertEqual(len(train), expected_train_length)
    #     self.assertEqual(len(test), expected_test_length)

    # def test_lag_series_default(self):
    #     # Test with the default lag of 1
    #     lagged_series = TimeseriesTests.lag_series(self.sample_series).reset_index(drop=True)
    #     expected_series = self.sample_series[:-1].reset_index(drop=True)
    #     self.assertTrue((lagged_series.values == expected_series.values).all())

    # def test_lag_series_custom_lag(self):
    #     # Test with a custom lag of 5
    #     lag = 5
    #     lagged_series = TimeseriesTests.lag_series(self.sample_series, lag=lag)
    #     self.assertEqual(len(lagged_series), len(self.sample_series) - lag)
    #     self.assertTrue((lagged_series.values == self.sample_series[:-lag].values).all())

    # def test_split_data_custom_ratio(self):
    #     custom_ratio = 0.7
    #     train, test = TimeseriesTests.split_data(self.sample_dataframe, train_ratio=custom_ratio)
    #     expected_train_length = int(len(self.sample_dataframe) * custom_ratio)
    #     expected_test_length = len(self.sample_dataframe) - expected_train_length
    #     self.assertEqual(len(train), expected_train_length)
    #     self.assertEqual(len(test), expected_test_length)

    # def test_split_data_data_integrity(self):
    #     train, test = TimeseriesTests.split_data(self.sample_dataframe)
    #     # Check if concatenated train and test sets equal the original data
    #     pd.testing.assert_frame_equal(pd.concat([train, test]).reset_index(drop=True), self.sample_dataframe)

    # def test_adf_mean_reverting(self):
    #     result = TimeseriesTests.adf_test(self.mean_reverting_series)
    #     # Expect mean-reverting series to be potentially stationary
    #     self.assertEqual(result['Stationarity'], 'Stationary')

    # def test_adf_trending(self):
    #     result = TimeseriesTests.adf_test(self.trending_series)
    #     # Expect trending series to be non-stationary
    #     self.assertEqual(result['Stationarity'], 'Non-Stationary')

    # def test_adf_random_walk(self):
    #     n=2000
    #     series = TimeseriesTests.generate_random_walk_series(n=n, start_value=0, step_std=1)
    #     result = TimeseriesTests.adf_test(series)

    #     # Expect random walk series to be non-stationary
    #     self.assertEqual(result['Stationarity'], 'Non-Stationary')

    # def test_kpss_mean_reverting(self):
    #     result = TimeseriesTests.kpss_test(self.mean_reverting_series)
    #     # Expect mean-reverting series to be potentially stationary
    #     self.assertEqual(result['Stationarity'], 'Stationary')

    # def test_kpss_trending(self):
    #     result = TimeseriesTests.kpss_test(self.trending_series)
    #     # Expect trending series to be non-stationary
    #     self.assertEqual(result['Stationarity'], 'Non-Stationary')

    # def test_kpss_random_walk(self):
    #     n=2000
    #     series = TimeseriesTests.generate_random_walk_series(n=n, start_value=0, step_std=1)
    #     result = TimeseriesTests.kpss_test(series)

    #     # Expect random walk series to be non-stationary
    #     self.assertEqual(result['Stationarity'], 'Non-Stationary')

    # def test_phillips_perron_mean_reverting(self):
    #     result = TimeseriesTests.phillips_perron_test(self.mean_reverting_series)
    #     # Expect mean-reverting series to be potentially stationary
    #     self.assertEqual(result['Stationarity'], 'Stationary')

    # def test_phillips_perron_trending(self):
    #     result = TimeseriesTests.phillips_perron_test(self.trending_series, trend='ct')
    #     # Expect trending series to be non-stationary
    #     self.assertEqual(result['Stationarity'], 'Non-Stationary')

    # def test_phillips_perron_random_walk(self):
    #     series = pd.Series(TimeseriesTests.generate_random_walk_series(n=2000, start_value=0, step_std=1))
    #     result = TimeseriesTests.phillips_perron_test(series)
    #     # Expect random walk series to be non-stationary
    #     self.assertEqual(result['Stationarity'], 'Non-Stationary')

    # def test_seasonal_stationary(self):
    #     """Test that the method identifies a seasonal stationary series as stationary."""
    #     series = generate_seasonal_stationary_series()
    #     result = TimeseriesTests.seasonal_adf_test(series, seasonal_periods=12)
    #     self.assertEqual(result['Stationarity'], 'Stationary', "Failed to identify a seasonal stationary series as stationary")

    # def test_non_seasonal_stationary(self):
    #     """Test that the method identifies a non-stationary series as non-stationary."""
    #     series = generate_seasonal_non_stationary_series()
    #     result = TimeseriesTests.seasonal_adf_test(series, seasonal_periods=12)
    #     self.assertEqual(result['Stationarity'], 'Non-Stationary', "Failed to identify a non-stationary series as non-stationary")
   
    # def test_johansen_test_cointegration(self):
    #     """Test the Johansen test can detect cointegration in a synthetic dataset."""
    #     data = generate_cointegrated_series()
    #     # test
    #     _, num_cointegrations = TimeseriesTests.johansen_test(data)
    #     # validation
    #     self.assertGreater(num_cointegrations,0)

    # def test_johansen_test_no_cointegration(self):
    #     """Test the Johansen test does not falsely detect cointegration."""
    #     data = generate_non_cointegrated_series()
    #     # Test
    #     _, num_cointegrations = TimeseriesTests.johansen_test(data)
    #     # Validation
    #     self.assertEqual(num_cointegrations, 0)
    
    # def test_select_lag_known_optimal_lag(self):
    #     """Test that the select_lag_length function identifies the expected optimal lag."""
    #     data = generate_random_time_series(lag=4)
    #     data.plot(figsize=(10, 6))
    #     plt.title('Time Series Data')
    #     plt.xlabel('Time')
    #     plt.ylabel('Value')
    #     plt.show()

    #     # Assuming we know the optimal lag for the synthetic data is around 2
    #     # This assumption needs to be adjusted based on how you generate your test data
    #     expected_lag = 4
    #     selected_lag = TimeseriesTests.select_lag_length(data, maxlags=10, criterion='bic')
    #     self.assertEqual(selected_lag, expected_lag, f"Expected optimal lag of {expected_lag}, but got {selected_lag}.")

    # def test_lag_selection_criteria(self):
    #     """Test the select_lag_length function with different information criteria."""
    #     data = generate_random_time_series()
    #     for criterion in ['aic', 'bic', 'hqic', 'fpe']:
    #         with self.subTest(criterion=criterion):
    #             selected_lag = TimeseriesTests.select_lag_length(data, maxlags=10, criterion=criterion)
    #             self.assertIsInstance(selected_lag, int, f"Selected lag should be an integer for criterion {criterion}.")
    #             self.assertTrue(1 <= selected_lag <= 10, f"Selected lag should be within the specified range for criterion {criterion}.")

    # def test_select_coint_rank_no_cointegration(self):
    #     """Test cointegration rank selection on non-cointegrated data."""
    #     data = generate_non_cointegrated_series()
    #     result = TimeseriesTests.select_coint_rank(data, k_ar_diff=1)
    #     self.assertEqual(result['Cointegration Rank'], 0, "Failed to correctly identify no cointegration.")

    # def test_select_coint_rank_potential_cointegration(self):
    #     """Test cointegration rank selection on potentially cointegrated data."""
    #     data = generate_cointegrated_series()
    #     result = TimeseriesTests.select_coint_rank(data, k_ar_diff=1)
    #     # Here, we expect some level of cointegration due to the common trend
    #     self.assertGreaterEqual(result['Cointegration Rank'], 1, "Failed to identify potential cointegration.")

    # def test_durbin_watson_no_autocorrelation(self):
    #     residuals = generate_residuals('none')
    #     result = TimeseriesTests.durbin_watson(residuals)
    #     self.assertIn('Absent', result['Residuals']['Autocorrelation'])

    # def test_durbin_watson_positive_autocorrelation(self):
    #     residuals = generate_residuals('positive')
    #     result = TimeseriesTests.durbin_watson(residuals)
    #     self.assertIn('Positive', result['Residuals']['Autocorrelation'])

    # def test_durbin_watson_negative_autocorrelation(self):
    #     residuals = generate_residuals('negative')
    #     result = TimeseriesTests.durbin_watson(residuals)
    #     self.assertIn('Negative', result['Residuals']['Autocorrelation'])

    # def test_ljung_box_no_autocorrelation(self):
    #     residuals = generate_residuals('none')
    #     result = TimeseriesTests.ljung_box(residuals, lags=10)
    #     self.assertEqual(result['Residuals']['Autocorrelation'], 'Absent', "Failed to correctly identify absence of autocorrelation")

    # def test_ljung_box_positive_autocorrelation(self):
    #     residuals = generate_residuals('positive')
    #     result = TimeseriesTests.ljung_box(residuals, lags=10)
    #     self.assertEqual(result['Residuals']['Autocorrelation'], 'Present', "Failed to correctly identify presence of autocorrelation")

    # def test_shapiro_wilk_normal_distribution(self):
    #     # Generate a normally distributed dataset
    #     data = pd.Series(np.random.normal(loc=0, scale=1, size=100))
    #     result = TimeseriesTests.shapiro_wilk(data)
    #     self.assertEqual(result['Normality'], 'Normal', "Failed to correctly identify a normal distribution")

    # def test_shapiro_wilk_non_normal_distribution(self):
    #     # Generate a uniformly distributed dataset
    #     data = pd.Series(np.random.uniform(low=-1, high=1, size=100))
    #     result = TimeseriesTests.shapiro_wilk(data)
    #     self.assertEqual(result['Normality'], 'Not Normal', "Failed to correctly identify a non-normal distribution")

    # def test_breusch_pagan_no_heteroscedasticity(self):
    #     # Simulate data with no heteroscedasticity
    #     np.random.seed(42)
    #     x = np.random.normal(size=(100, 2))
    #     y = 2 + 3 * x[:, 0] + 4 * x[:, 1] + np.random.normal(size=100)
    #     result = TimeseriesTests.breusch_pagan(x, y)
    #     self.assertEqual(result['Heteroscedasticity'], 'Absent', "Failed to correctly identify absence of heteroscedasticity")

    # def test_breusch_pagan_heteroscedasticity(self):
    #     # Simulate data with heteroscedasticity
    #     np.random.seed(42)
    #     x = np.random.normal(size=(100, 2))

    #     # Heteroscedasticity introduced more strongly
    #     y = 2 + 3 * x[:, 0] + 4 * x[:, 1] + np.random.normal(size=100) * (1 + x[:, 0])
    #     result = TimeseriesTests.breusch_pagan(x, y)
    #     self.assertEqual(result['Heteroscedasticity'], 'Present', "Failed to correctly identify presence of heteroscedasticity")

    # def test_white_homoscedasticity(self):
    #     # Simulate data with homoscedastic residuals
    #     np.random.seed(42)
    #     x = np.random.normal(size=(100, 2))
    #     y = 2 + 3 * x[:, 0] + 4 * x[:, 1] + np.random.normal(size=100)
    #     result = TimeseriesTests.white_test(x, y)
    #     self.assertEqual(result['Heteroscedasticity'], 'Absent', "Failed to correctly identify homoscedastic residuals")

    # def test_white_heteroscedasticity(self):
    #     # Simulate data with heteroscedastic residuals
    #     np.random.seed(42)
    #     x = np.random.normal(size=(100, 2))
    #     y = 2 + 3 * x[:, 0] + 4 * x[:, 1] + np.random.normal(size=100) * (5 * abs(x[:, 0]))
    #     result = TimeseriesTests.white_test(x, y)
    #     self.assertEqual(result['Heteroscedasticity'], 'Present', "Failed to correctly identify heteroscedastic residuals")

    # def test_granger_causality_x_to_y(self):
    #     data = generate_causal_data()
    #     result = TimeseriesTests.granger_causality(data, max_lag=10, significance_level=0.05)
    #     self.assertEqual(result[('x', 'y')]['Granger Causality'], 'Causality')

    # def test_granger_causality_y_to_x(self):
    #     data = generate_causal_data()
    #     result = TimeseriesTests.granger_causality(data, max_lag=10, significance_level=0.05)
    #     self.assertEqual(result[('y', 'x')]['Granger Causality'], 'Non-Causality')

    def test_hurst_exp_mean_reverting_series(self):
        hurst = TimeseriesTests.hurst_exponent(self.mean_reverting_series)
        self.assertLess(hurst, 0.5)

    def test_hurst_exp_random_walk(self):
        series = TimeseriesTests.generate_random_walk_series()
        hurst = TimeseriesTests.hurst_exponent(series)
        self.assertAlmostEqual(hurst, 0.5, delta=0.05)
        
    def test_hurst_exp_trending_series(self):
        self.trending_series = TimeseriesTests.generate_trending_series()
        
        hurst = TimeseriesTests.hurst_exponent(self.trending_series)
        self.assertGreater(hurst, 0.5)

    # def test_half_life_valid(self):
    #     """
    #     Test the half_life function with a known half-life.
    #     """
    #     known_half_life = 10  # Known half-life of the series
    #     series = generate_mean_reverting_series_known_half_life(half_life=known_half_life)
        
    #     # Create a lagged version of the series
    #     series_lagged = series.shift(1).bfill() 
        
    #     # Calculate the half-life using the function under test
    #     calculated_half_life, _ = TimeseriesTests.half_life(series, series_lagged, include_constant=False)
        
    #     # Assert the calculated half-life is close to the known value
    #     self.assertAlmostEqual(known_half_life, calculated_half_life, delta=1, msg="Calculated half-life deviates from the known value")

    # def test_evaluate_forecast_dataframe(self):
    #     """Test the evaluate_forecast function with pd.DataFrame input."""
    #     # For DataFrame testing
    #     self.actual = pd.Series(np.random.normal(100, 10, 100), name='TestSeries')
    #     self.forecast = self.actual + np.random.normal(0, 5, 100)  # Adding noise to create a forecast

    #     self.actual_df = pd.DataFrame({
    #         'Series1': self.actual,
    #         'Series2': self.actual + np.random.normal(0, 3, 100)  # Another series with less noise
    #     })
    #     self.forecast_df = pd.DataFrame({
    #         'Series1': self.forecast,
    #         'Series2': self.actual_df['Series2'] + np.random.normal(0, 2, 100)  # Forecast with different noise
    #     })
    #     result = TimeseriesTests.evaluate_forecast(self.actual_df, self.forecast_df, print_output=False)
    #     self.assertIsInstance(result, dict, "The result should be a dictionary.")
    #     for col in self.actual_df.columns:
    #         self.assertIn(col, result, f"Result dictionary should include metrics for {col}.")
    #         self.assertIn('MAE', result[col], f"Result for {col} should include MAE.")
    #         self.assertIn('MSE', result[col], f"Result for {col} should include MSE.")
    #         self.assertIn('RMSE', result[col], f"Result for {col} should include RMSE.")
    #         self.assertIn('MAPE', result[col], f"Result for {col} should include MAPE.")

    # def test_evaluate_forecast_series(self):
    #     """Test the evaluate_forecast function with pd.Series input."""
    #     self.actual = pd.Series(np.random.normal(100, 10, 100), name='TestSeries')
    #     self.forecast = self.actual + np.random.normal(0, 5, 100)  # Adding noise to create a forecast

    #     result = TimeseriesTests.evaluate_forecast(self.actual, self.forecast, print_output=False)

    #     self.assertIsInstance(result, dict, "The result should be a dictionary.")
    #     self.assertIn('MAE', result['TestSeries'], "Result dictionary should include MAE.")
    #     self.assertIn('MSE', result['TestSeries'], "Result dictionary should include MSE.")
    #     self.assertIn('RMSE', result['TestSeries'], "Result dictionary should include RMSE.")
    #     self.assertIn('MAPE', result['TestSeries'], "Result dictionary should include MAPE.")
            

if __name__ =="__main__":
    unittest.main()
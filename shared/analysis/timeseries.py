import warnings
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from arch.unitroot import PhillipsPerron
from sklearn.metrics import mean_absolute_error, mean_squared_error

import statsmodels.api as sm
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.stats.diagnostic import het_breuschpagan, het_white
from statsmodels.tsa.vector_ar.vecm import coint_johansen, VECM, select_coint_rank

import scipy.stats as stats
from scipy.stats import norm
from scipy.stats import shapiro
from scipy.optimize import curve_fit


pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000) # Adjust the width of the display in characters
pd.set_option('display.max_rows', None)


class TimeseriesTests:
    """
    Easy use and display of the results from statsmodels tests, for timerseries analysis.
    """
    # -- Synthentic Timeseries --
    @staticmethod
    def generate_mean_reverting_series(n=2000, mu=0, theta=0.1 , sigma=0.2, start_value=1):
        """
        Generate a mean-reverting time series using the Ornstein-Uhlenbeck process.

        Parameters:
        n (int): The number of observations in the time series.
        mu (float): The long-term mean value towards which the time series reverts.
        theta (float): The rate of reversion to the mean.
        sigma (float): The volatility of the process.
        start_value (float): The starting value of the time series.

        Returns:
        np.array: A numpy array representing the generated time series.
        """
        time_series = [start_value]
        for _ in range(1, n):
            dt = 1  # Time step
            previous_value = time_series[-1]
            random_term = np.random.normal(loc=0.0, scale=np.sqrt(dt) * sigma)
            next_value = previous_value + theta * (mu - previous_value) * dt + random_term
            time_series.append(next_value)

        return np.array(time_series)

    @staticmethod
    def generate_trending_series(n=2000, start_value=0, trend=5, step_std=1):
        """
        Generate a trending time series.

        Parameters:
        n (int): The number of observations in the time series.
        start_value (float): The starting value of the time series.
        trend (float): The constant amount added to each step to create a trend.
        step_std (float): The standard deviation of the step size.

        Returns:
        np.array: A numpy array representing the generated time series.
        """
        time_series = [start_value]
        for _ in range(1, n):
            step = np.random.normal(scale=step_std) + trend
            next_value = time_series[-1] + step
            time_series.append(next_value)

        return np.array(time_series)

    @staticmethod
    def generate_random_walk_series(n=2000, start_value=0, step_std=1):
        """
        Generate a random walk time series.

        Parameters:
        n (int): The number of observations in the time series.
        start_value (float): The starting value of the time series.
        step_std (float): The standard deviation of the step size.

        Returns:
        np.array: A numpy array representing the generated time series.
        """
        time_series = [start_value]
        for _ in range(1, n):
            step = np.random.normal(scale=step_std)
            next_value = time_series[-1] + step
            time_series.append(next_value)

        return np.array(time_series)
    
    # -- Timeseries Adjustment -- 
    @staticmethod
    def lag_series(series: pd.Series, lag: int = 1):
        """Lags a pandas series by a given lag. Default lag = 1."""
        # Create a lagged version of the series
        series_lagged = series.shift(lag)

        # Remove NaN values and reset the index
        series_lagged = series_lagged[lag:].reset_index(drop=True)

        return series_lagged
    
    @staticmethod
    def split_data(data:pd.DataFrame,train_ratio=0.8):
        split_index = int(len(data) * train_ratio)
        train_data = data.iloc[:split_index]
        test_data = data.iloc[split_index:]
        return train_data, test_data
    
    # -- Stationarity -- 
    @staticmethod
    def adf_test(series: pd.Series, trend='c', confidence_interval='5%', significance_level=0.05):
        """
        Perform the Augmented Dickey-Fuller (ADF) test to determine the stationarity of a time series.

        The null hypothesis (H0) of the ADF test posits that the time series has a unit root, indicating it is non-stationary.
        The alternative hypothesis (H1) suggests that the series is stationary.

        The test rejects the null hypothesis (and thus indicates stationarity) under two conditions:
        1. The ADF statistic is less than the critical value at the specified confidence interval.
        2. The p-value is less than the specified significance level, suggesting the result is statistically significant.

        Args:
        series (pd.Series): The time series to be tested.
        trend (str): Type of regression applied in the test. Options include:
            - 'c': Only a constant (default). Use if the series is expected to be stationary around a mean.
            - 'ct': Constant and trend. Use if the series is suspected to have a trend.
        confidence_interval (str): Confidence interval for the critical values. Common options are '1%', '5%', and '10%'.
        significance_level (float): The significance level for determining statistical significance. Default is 0.05.

        Returns:
        dict: A dictionary with the ADF test statistic, p-value, critical values, and an indication of stationarity 
        ('Stationary' or 'Non-Stationary') based on the test results.

        Note: A low p-value (less than the specified significance level) combined with an ADF statistic lower than the 
        critical value at the specified confidence interval suggests rejecting the null hypothesis in favor of stationarity. 
        Conversely, a high p-value suggests failing to reject the null hypothesis, indicating non-stationarity.
        """

        result = adfuller(x=series, regression=trend)
        adf_statistic = result[0]
        p_value = result[1]
        critical_values = result[4]

        # Prepare the results in a clean format
        output = {
            'ADF Statistic': adf_statistic,
            'p-value': p_value,
            'Critical Values': critical_values,
            'Stationarity': ''
        }

        # Determine stationarity based on the specified confidence interval and p-value
        stationarity = adf_statistic < critical_values[confidence_interval] and p_value < significance_level

        output['Stationarity'] = 'Stationary' if stationarity else 'Non-Stationary'

        return output

    @staticmethod
    def display_adf_results(adf_results:dict, print_output: bool = True, to_html: bool = False, indent: int=0):
        # Define the base indentation as a string of spaces
        base_indent = "    " * indent
        next_indent = "    " * (indent + 1)  

        # Convert ADF results to DataFrame
        adf_data = []
        for ticker, values in adf_results.items():
            row = {'Ticker': ticker, 'ADF Statistic': values['ADF Statistic'], 'p-value': round(values['p-value'],6)}
            row.update({f'Critical Value ({key})': val for key, val in values['Critical Values'].items()})
            row.update({'Stationarity': values['Stationarity']})
            adf_data.append(row)

        title = "ADF Test Results"
        adf_df = pd.DataFrame(adf_data)
        footer = "** IF p-value < 0.05 and/or statistic < statistic @ confidence interval, then REJECT the Null that the time series posses a unit root (non-stationary)."

        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = adf_df.to_html(index=False, border=1)
            html_table_indented = "\n".join(next_indent + line for line in html_table.split("\n"))

            html_title = f"{next_indent}<h2>{title}</h2>\n"
            html_footer = f"{next_indent}<p>{footer}</p>\n"
            html_output = f"{base_indent}<div>\n{html_title}{html_table_indented}\n{html_footer}{base_indent}</div>"
        
            return html_output
        
        elif print_output:
            print(f"""\n{title}:
                    {'=' * len(title)}
                    {adf_df}
                    {footer}
                """)
        else:
            return (
                f"\n{title}\n"
                f"{'=' * len(title)}\n"
                f"{adf_df.to_string(index=False)}\n"
                f"{footer}"
            )
    
    @staticmethod
    def kpss_test(series: pd.Series,trend='c', confidence_interval='5%'):
        """
        Perform the KPSS test to determine the stationarity of a time series.

        Null Hypothesis (H0): The series is stationary around a deterministic trend (level or trend stationarity).
        Alternative Hypothesis (H1): The series has a unit root (is non-stationary).

        Unlike other tests, a high p-value in the KPSS test suggests failure to reject the null hypothesis, indicating 
        stationarity. Conversely, a low p-value suggests rejecting the null hypothesis in favor of the alternative, 
        indicating non-stationarity.

        Args:
        series (pd.Series): The time series to be tested.
        trend (str): Type of regression applied in the test. Options include:
            - 'c': Only a constant. Use if the series is expected to be stationary around a mean.
            - 'ct': Constant and trend. Use if the series is suspected to have a trend and is stationary around a trend.
        significance_level (float): The significance level for determining statistical significance. This is used to 
        adjust the interpretation of the test result but note that KPSS uses critical values directly for decision making.

        Returns:
        dict: A dictionary with the KPSS test statistic, p-value, critical values, and an indication of stationarity 
        ('Stationary' or 'Non-Stationary') based on the test results. Stationarity is determined by comparing the test 
        statistic to critical values, not directly by p-value.

        Note: KPSS test results are interpreted differently from tests like ADF. Here, stationarity is suggested by not 
        rejecting the null hypothesis (high p-value), while evidence of non-stationarity comes from rejecting H0 (low p-value).
        """
        try:
            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter("always")
                kpss_statistic, p_value, n_lags, critical_values = kpss(series, regression=trend)

                # Check for specific KPSS warning about the p-value being outside the lookup table range
                for warning in caught_warnings:
                    if "p-value is smaller than the p-value returned" in str(warning.message):
                        p_value = 0.0  # Adjust p-value to indicate strong evidence of non-stationarity

        except ValueError as e:
            raise ValueError(f"KPSS test encountered an error: {e}")


        # Prepare the results in a structured format
        output = {
            'KPSS Statistic': kpss_statistic,
            'p-value': p_value,
            'Critical Values': critical_values,
            'Stationarity': ''
        }

        # Determine stationarity based on the 1% confidence interval
        stationarity = kpss_statistic < critical_values[confidence_interval]

        output['Stationarity'] = 'Stationary' if stationarity else 'Non-Stationary'

        return output
    
    @staticmethod
    def display_kpss_results(kpss_results:dict, print_output: bool=True, to_html: bool = False):
        # Convert KPSS results to DataFrame
        kpss_data = []
        for ticker, values in kpss_results.items():
            row = {'Ticker': ticker, 'KPSS Statistic': values['KPSS Statistic'], 'p-value': round(values['p-value'],6)}
            row.update({f'Critical Value ({key})': val for key, val in values['Critical Values'].items()})
            row.update({'Stationarity': values['Stationarity']})
            kpss_data.append(row)

        title = "KPSS Test Results"
        kpss_df = pd.DataFrame(kpss_data)
        footer = "** IF KPSS statistic > statistic @ confidence interval, then reject the NUll that time-series is stationary.\n"

        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = kpss_df.to_html(index=False, border=1)
            html_explanation = f"<p>{footer}</p>"
            html_output = f"<h2>{title}</h2>\n{html_table}\n{html_explanation}"
            return html_output
        elif print_output:
            print(f"""\n{title}:
                    {'=' * len(title)}
                    {kpss_df}
                    {footer}
                """)
        else:
            return (
                f"\n{title}\n"
                f"{'=' * len(title)}\n"
                f"{kpss_df.to_string(index=False)}\n"
                f"{footer}"
            )

    @staticmethod
    def phillips_perron_test(series: pd.Series, trend='c', confidence_interval='5%', significance_level=0.05):
        """
        Perform the Phillips-Perron test to determine the stationarity of a time series.

        The null hypothesis (H0) of the Phillips-Perron (PP) test posits that the time series has a unit root, 
        indicating it is non-stationary. The alternative hypothesis (H1) suggests that the series is stationary.

        The test rejects the null hypothesis (and thus indicates stationarity) under two conditions:
        1. The PP statistic is less than the critical value at the specified confidence interval.
        2. The p-value is less than the specified significance level, suggesting the result is statistically significant.

        Args:
        series (pd.Series): The time series to be tested.
        trend (str): Type of regression applied in the test. Options include:
            - 'c': Only a constant (default). Use if the series is expected to be stationary around a mean.
            - 'ct': Constant and trend. Use if the series is suspected to have a trend.
        confidence_interval (str): Confidence interval for the critical values. Common options are '1%', '5%', and '10%'.
        significance_level (float): The significance level for determining statistical significance. Default is 0.05.

        Returns:
        dict: A dictionary with the PP test statistic, p-value, critical values, and an indication of stationarity 
        ('Stationary' or 'Non-Stationary') based on the test results.

        Note: A low p-value (less than the specified significance level) combined with a PP statistic lower than the 
        critical value at the specified confidence interval suggests rejecting the null hypothesis in favor of stationarity. 
        Conversely, a high p-value suggests failing to reject the null hypothesis, indicating non-stationarity.
        """
        pp_test = PhillipsPerron(series, trend=trend)
        pp_statistic = pp_test.stat
        p_value = pp_test.pvalue
        critical_values = pp_test.critical_values

        # Prepare the results in a clean format
        output = {
            'PP Statistic': pp_statistic,
            'p-value': p_value,
            'Critical Values': critical_values,
            'Stationarity': ''
        }

        # Determine stationarity based on the specified confidence interval and p-value
        stationarity = pp_statistic < critical_values[confidence_interval] and p_value < significance_level

        output['Stationarity'] = 'Stationary' if stationarity else 'Non-Stationary'

        return output

    @staticmethod
    def display_pp_results(pp_results: dict, print_output: bool=True, to_html: bool = False, indent: int=0):
        # Define the base indentation as a string of spaces
        base_indent = "    " * indent
        next_indent = "    " * (indent + 1)  

        # Convert PP results to DataFrame
        pp_data = []
        for ticker, values in pp_results.items():
            row = {
                'Ticker': ticker, 
                'PP Statistic': values['PP Statistic'], 
                'p-value': round(values['p-value'], 6)
            }
            row.update({f'Critical Value ({key}%)': val for key, val in values['Critical Values'].items()})
            row.update({'Stationarity': values['Stationarity']})
            pp_data.append(row)

        title = "Phillips Perron Results"
        pp_df = pd.DataFrame(pp_data)
        footer = "** IF p-value < 0.05, then REJECT the Null Hypothesis of a unit root (non-stationary time series)."

        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = pp_df.to_html(index=False, border=1)
            html_table_indented = "\n".join(next_indent + line for line in html_table.split("\n"))

            html_title = f"{next_indent}<h2>{title}</h2>\n"
            html_footer = f"{next_indent}<p>{footer}</p>\n"
            html_output = f"{base_indent}<div>\n{html_title}{html_table_indented}\n{html_footer}{base_indent}</div>"
        
            return html_output

        elif print_output:
            print(f"""\n{title}:
                    {'=' * len(title)}
                    {pp_df}
                    {footer}
                """)
        else:
            return (
                f"\n{title}\n"
                f"{'=' * len(title)}\n"
                f"{pp_df.to_string(index=False)}\n"
                f"{footer}"
            )
        
    @staticmethod
    def seasonal_adf_test(series: pd.Series, maxlag: int = None, regression: str = 'c', seasonal_periods: int = 12, confidence_interval: str = '5%', significance_level=0.05) -> dict:
        """
        Perform Seasonal Augmented Dickey-Fuller (ADF) test to assess the stationarity of a seasonal time series.

        The test decomposes the series into seasonal, trend, and residual components, and then performs the ADF test
        on the detrended series. This method helps in identifying whether the time series is stationary, taking into
        account its seasonality.

        Parameters:
            series (pd.Series): Time series data.
            maxlag (int, optional): Maximum number of lags to include in the ADF test. Defaults to None, letting the
                                    test choose the lag based on AIC.
            regression (str, optional): Type of regression ('c' constant, 'ct' constant and trend, 'ctt' constant,
                                        trend, and trend squared, 'nc' no constant). Defaults to 'c'.
            seasonal_periods (int, optional): Number of periods in a season. Defaults to 12.
            confidence_interval (str, optional): The confidence interval used to determine stationarity. Defaults to '5%'.

        Returns:
            dict: A dictionary with the test statistic ('ADF Statistic'), the p-value ('p-value'), the critical values
                ('Critical Values'), and an indication of stationarity ('Stationarity') based on the specified 
                confidence interval.

        Raises:
            ValueError: If the series is empty or contains fewer observations than the seasonal_periods.
        """
        if series.empty or len(series) < seasonal_periods:
            raise ValueError("The time series must contain more observations than the number of seasonal periods.")
        
        # Seasonal decomposition
        dftest = sm.tsa.seasonal_decompose(series, model='additive', period=seasonal_periods)
        detrended = series - dftest.trend  # Remove the trend component

        # Perform the ADF test on the detrended series
        result = sm.tsa.adfuller(detrended.dropna(), maxlag=maxlag, regression=regression, autolag='AIC')

        adf_statistic, p_value, _, _, critical_values, _ = result
        
        # Determine stationarity
        stationarity = 'Stationary' if adf_statistic < critical_values[confidence_interval] and p_value < significance_level else 'Non-Stationary'

        return {
            'ADF Statistic': adf_statistic,
            'p-value': p_value,
            'Critical Values': critical_values,
            'Stationarity': stationarity
        }

    # -- Cointegration --
    @staticmethod
    def johansen_test(data: pd.DataFrame, det_order: int = -1, k_ar_diff: int = 1) -> dict:
        """
        Perform Johansen cointegration test to assess the presence of cointegration relationships 
        among several time series.

        The Johansen test helps to determine the number of cointegrating relationships in a system 
        of multiple time series.

        Parameters:
            data (pd.DataFrame): A pandas DataFrame where each column represents a time series.
            det_order (int): Specifies the deterministic trend in the data. The default value is -1,
                            which includes a constant term but no trend. 0 includes no constant or trend,
                            and 1 includes a constant and a linear trend.
            k_ar_diff (int): The number of lagged differences used in the test. The default is 1.

        Returns:
            dict: A dictionary containing the test's eigenvalues, critical values, statistics, and 
                the cointegrating vector. It also includes analysis of trace and max eigenvalue statistics.

        Raises:
            ValueError: If `data` is empty or not a pandas DataFrame.
        """
        if data.empty or not isinstance(data, pd.DataFrame):
            raise ValueError("Input data must be a non-empty pandas DataFrame.")

        # Perform the Johansen cointegration test
        result = coint_johansen(data, det_order, k_ar_diff)

        # Structured results
        output = {
            'Eigenvalues': result.eig,
            'Critical Values for Trace Statistic': result.cvt[:, 0],
            'Critical Values for Max Eigenvalue Statistic': result.cvt[:, 1],
            'Trace Statistics': result.lr1,
            'Max Eigenvalue Statistics': result.lr2,
            'Cointegrating Vector': result.evec.T.tolist()  # Transpose to list for readability
        }
        # Analysis of Trace and Max Eigenvalue Statistics
        num_cointegrations = 0
        trace_analysis = []
        max_eig_analysis = []

        for idx, (trace_stat, max_eig_stat) in enumerate(zip(output['Trace Statistics'], output['Max Eigenvalue Statistics'])):
            trace_crit_value = output['Critical Values for Trace Statistic'][idx]
            max_eig_crit_value = output['Critical Values for Max Eigenvalue Statistic'][idx]

            trace_decision = trace_stat > trace_crit_value
            max_eig_decision = max_eig_stat > max_eig_crit_value

            trace_analysis.append(f'Hypothesis {idx}: {"Reject" if trace_decision else "Fail to Reject"} the null hypothesis of no cointegration at this level.')
            max_eig_analysis.append(f'Hypothesis {idx}: {"Reject" if max_eig_decision else "Fail to Reject"} the null hypothesis of no cointegration at this level.')

            if trace_decision and max_eig_decision:
                num_cointegrations += 1


        return output, num_cointegrations
    
    @staticmethod
    def display_johansen_results(johansen_results: dict, num_cointegrations: int, print_output: bool=True, to_html: bool=False, indent: int=0):
        # Define the base indentation as a string of spaces
        base_indent = "    " * indent
        next_indent = "    " * (indent + 1)  
    
        # Creating DataFrame from the results
        johansen_df = pd.DataFrame({
            'Hypothesis': [f'H{i}' for i in range(len(johansen_results['Eigenvalues']))],
            'Eigenvalue': johansen_results['Eigenvalues'],
            'Trace Statistic': johansen_results['Trace Statistics'],
            'Critical Value (Trace)': johansen_results['Critical Values for Trace Statistic'],
            'Max Eigenvalue Statistic': johansen_results['Max Eigenvalue Statistics'],
            'Critical Value (Max Eigenvalue)': johansen_results['Critical Values for Max Eigenvalue Statistic'],
        })

        # Add decision columns based on comparisons
        johansen_df['Decision (Trace)'] = johansen_df.apply(
            lambda row: 'Reject' if row['Trace Statistic'] > row['Critical Value (Trace)'] else 'Fail to Reject',
            axis=1
        )
        johansen_df['Decision (Max Eigenvalue)'] = johansen_df.apply(
            lambda row: 'Reject' if row['Max Eigenvalue Statistic'] > row['Critical Value (Max Eigenvalue)'] else 'Fail to Reject',
            axis=1
        )
        
        title = "Johansen Cointegration Test Results"
        header = f"Number of cointerated realtionships : {num_cointegrations}"
        footer = f"** IF Trace Statistic > Critical Value AND Max Eigenvalue > Critical Value then Reject Null of at most r cointegrating relationships.(r=0 in first test)"

        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = johansen_df.to_html(index=False, border=1)
            html_table_indented = "\n".join(next_indent + line for line in html_table.split("\n"))

            # Construct the complete HTML output with proper indentation
            html_title = f"{next_indent}<h2>{title}</h2>\n"
            html_header = f"{next_indent}<p>{header}</p>\n"
            html_footer = f"{next_indent}<p>{footer}</p>\n"
            html_output = f"{base_indent}<div>\n{html_title}{html_header}{html_table_indented}\n{html_footer}{base_indent}</div>"
        
            return html_output
        
        elif print_output:
            print(f"""\n{title}:
                    {'=' * len(title)}
                    {header}
                    {johansen_df}
                    {footer}
                """)
        else:
            return (
                f"\n{title}\n"
                f"{'=' * len(title)}\n"
                f"{header}\n"
                f"{johansen_df.to_string(index=False)}\n"
                f"{footer}"
            )
        
    @staticmethod
    def select_lag_length(data: pd.DataFrame, maxlags: int = 10, criterion: str = 'bic') -> int:
        """
        Selects the optimal lag length for a time series dataset based on a specified information criterion.

        This method fits Vector AutoRegression (VAR) models with different lags up to a specified maximum. 
        It evaluates each model based on the chosen information criterion (AIC, BIC, FPE, or HQIC) 
        and selects the lag length that minimizes the criterion value.
        **Note: BIC will be more conservative and less overfitted than AIC

        Parameters:
            data (pd.DataFrame): A pandas DataFrame containing the time series data.
            maxlags (int, optional): The maximum number of lags to test. Defaults to 10.
            criterion (str, optional): The information criterion to use for selecting the optimal lag.
                                    Options are 'aic' (default), 'bic', 'fpe', and 'hqic'.

        Returns:
            int: The optimal number of lags according to the specified information criterion.

        Raises:
            ValueError: If the input data is not a pandas DataFrame or is empty.
                        If the specified criterion is not supported.
        """
        if not isinstance(data, pd.DataFrame) or data.empty:
            raise ValueError("Data must be a non-empty pandas DataFrame.")

        if criterion not in ['aic', 'bic', 'fpe', 'hqic']:
            raise ValueError(f"Unsupported criterion '{criterion}'. Choose from 'aic', 'bic', 'fpe', or 'hqic'.")

        # Initialize variables to store the best lag and its corresponding criterion value
        best_lag = 0
        best_criterion = float('inf')

        # Iterate over possible lag values
        for lag in range(1, maxlags + 1):
            model = VAR(data)
            result = model.fit(lag)

            # Retrieve the criterion value based on the user's choice
            criterion_value = getattr(result, criterion)

            # Update the best lag if this criterion value is the best so far
            if criterion_value < best_criterion:
                best_criterion = criterion_value
                best_lag = lag

        return best_lag
    
    @staticmethod
    def select_coint_rank(data: pd.DataFrame, k_ar_diff: int, method: str = 'trace', signif: float = 0.05, det_order: int = -1):
        """
        Selects the cointegration rank for a dataset using the Johansen cointegration test.

        Parameters:
            data (pd.DataFrame): A pandas DataFrame containing the time series data.
            k_ar_diff (int): The number of lags minus one to be used in the Johansen test.
            method (str, optional): The test statistic to use ('trace' or 'maxeig'). Defaults to 'trace'.
            signif (float, optional): Significance level for rejecting the null hypothesis. Defaults to 0.05.
            det_order (int, optional): The order of the deterministic trend to include in the test. 
                                    -1 for no deterministic term, 0 for constant term only, and 1 for constant with linear trend. 
                                    Defaults to -1.

        Returns:
            A summary of the Johansen cointegration test results, including the selected cointegration rank based on the specified significance level.

        Raises:
            ValueError: If `data` is not a pandas DataFrame or if other input parameters do not meet the required conditions.
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame.")
        if method not in ['trace', 'maxeig']:
            raise ValueError("Method must be either 'trace' or 'maxeig'.")
        if not (0 < signif < 1):
            raise ValueError("Signif must be between 0 and 1.")
        if det_order not in [-1, 0, 1]:
            raise ValueError("det_order must be -1, 0, or 1.")
        
        result = select_coint_rank(data, det_order=det_order, k_ar_diff=k_ar_diff, method=method, signif=signif)
        
        # Format the results for clearer interpretation
        summary = {
            'Cointegration Rank': result.rank,
            'Test Statistic': result.test_stats,
            'Critical Value': result.crit_vals,
            'Significance Level': signif,
            'Method': method
        }
        
        return summary
    
    # -- Autocorrelation -- 
    @staticmethod
    def durbin_watson(residuals: pd.DataFrame):
        """
        Perform the Durbin-Watson test to assess autocorrelation in the residuals of a regression model.

        The Durbin-Watson statistic ranges from 0 to 4, where:
        - A value of approximately 2 indicates no autocorrelation.
        - Values less than 2 suggest positive autocorrelation.
        - Values greater than 2 indicate negative autocorrelation.

        The closer the statistic is to 0, the stronger the evidence for positive serial correlation. Conversely,
        the closer to 4, the stronger the evidence for negative serial correlation.

        Args:
        residuals (pd.DataFrame): A pandas DataFrame of residuals from a regression model, where each column represents 
                                a different set of residuals (e.g., from multiple models or dependent variables).

        Returns:
        dict: A dictionary with column names as keys and values as another dictionary containing the Durbin-Watson statistic
            and an interpretation of autocorrelation ('Positive', 'Negative', or 'Absent').
        """
        dw_stats = {}
        for col in residuals.columns:
            dw_stat = durbin_watson(residuals[col])
            # Interpret the Durbin-Watson statistic
            autocorrelation = 'Absent'
            if dw_stat < 1.5:
                autocorrelation = 'Positive'
            elif dw_stat > 2.5:
                autocorrelation = 'Negative'

            dw_stats[col] = {
                'Durbin-Watson Statistic': dw_stat,
                'Autocorrelation': autocorrelation
            }
        return dw_stats

    @staticmethod 
    def display_durbin_watson_results(dw_results:dict, print_output: bool=True, to_html: bool = False):
        # Convert Durbin-Watson results to DataFrame
        dw_data = []
        for ticker, values in dw_results.items():
            row = {
                'Ticker': ticker, 
                'Durbin-Watson Statistic': values['Durbin-Watson Statistic'], 
                'Autocorrelation': values['Autocorrelation']
            }
            dw_data.append(row)

        dw_df = pd.DataFrame(dw_data)
        footnote = "** If the Durbin-Watson statistic is significantly different from 2 (either much less than 2 or much greater than 2), it suggests the presence of autocorrelation in the residuals.\n"

        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = dw_df.to_html(index=False, border=1)
            html_explanation = f"<p>{footnote}</p>"
            html_output = f"<h2>Durbin Watson Results</h2>\n{html_table}\n{html_explanation}"
            return html_output
        elif print_output:
            print(f"Durbin Watson Results:\n{dw_df}\n{footnote}")
        else:
            return f"Durbin Watson Results:\n{dw_df.to_string(index=False)}\n{footnote}"
    
    @staticmethod
    def ljung_box(residuals: pd.DataFrame, lags: int, significance_level: float = 0.05):
        """
        Perform the Ljung-Box test to assess the presence of autocorrelation at multiple lag levels 
        in the residuals of a regression model.

        This test is useful for checking randomness in a time series. The null hypothesis suggests 
        that autocorrelations of the residual time series are absent, i.e., the data are independently distributed. 
        Rejection of the null hypothesis indicates the presence of autocorrelation.

        Args:
        residuals (pd.DataFrame): A pandas DataFrame of residuals from a regression model, 
                                where each column represents a different set of residuals 
                                (e.g., from multiple models or dependent variables).
        lags (int): The number of lags to include in the test. Can also be an array of integers specifying the lags.
        significance_level (float): The significance level for determining the presence of autocorrelation. 
                                    Default is 0.05.

        Returns:
        dict: A dictionary with column names as keys and values as dictionaries containing the Ljung-Box 
            test statistics, p-values, a boolean array indicating which lags are significantly autocorrelated, 
            and an overall indication of autocorrelation ('Present' or 'Absent') based on the test results.
        """
        lb_results = {}
        for col in residuals.columns:
            lb_test = acorr_ljungbox(residuals[col], lags=lags, return_df=True)
            is_autocorrelated = any(lb_test['lb_pvalue'] < significance_level)
            lb_results[col] = {
                'test_statistic': lb_test['lb_stat'].to_list(),
                'p_value': lb_test['lb_pvalue'].to_list(),
                'significance': (lb_test['lb_pvalue'] < significance_level).to_list(),
                'Autocorrelation': 'Present' if is_autocorrelated else 'Absent'
            }
        return lb_results

    @staticmethod
    def display_ljung_box_results(ljung_box_results:dict, print_output: bool=True, to_html: bool = False):
        # Convert Ljung-Box results to DataFrame
        ljung_box_data = []
        for ticker, values in ljung_box_results.items():
            row = {'Ticker': ticker, 'Test Statistic': values['test_statistic'][0], 'p-value': round(values['p_value'][0], 6)}
            row.update({'Autocorrelation': 'Absent' if values['significance'][0] == False else 'Present'})
            ljung_box_data.append(row)

        ljung_box_df = pd.DataFrame(ljung_box_data)
        footnote = "** IF p-value < 0.05, then REJECT the Null Hypothesis of no autocorrelation (i.e., autocorrelation is present).\n"
    
        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = ljung_box_df.to_html(index=False, border=1)
            html_explanation = f"<p>{footnote}</p>"
            html_output = f"<h2>Ljung-Box Results</h2>\n{html_table}\n{html_explanation}"
            return html_output
        elif print_output:
            print(f"Ljung-Box Results:\n{ljung_box_df}\n{footnote}")
        else:
            return f"Ljung-Box Results:\n{ljung_box_df.to_string(index=False)}\n{footnote}"
    
    # -- Normality -- 
    @staticmethod
    def shapiro_wilk(data: pd.Series, significance_level: float = 0.05):
        """
        Perform the Shapiro-Wilk test to assess the normality of a dataset.

        The Shapiro-Wilk test evaluates the null hypothesis that the data was drawn from a normal distribution.
        
        Args:
            data (pd.Series or array-like): The dataset to test for normality. Should be one-dimensional.
            significance_level (float): The significance level at which to test the null hypothesis. Default is 0.05.

        Returns:
            dict: A dictionary containing the test statistic ('Statistic'), the p-value ('p-value'), and an indication
                of whether the data is considered 'Normal' or 'Not Normal' based on the significance level.

        Raises:
            ValueError: If the input data contains fewer than 3 elements, as the test cannot be applied in such cases.
        """
        if len(data) < 3:
            raise ValueError("Data must contain at least 3 elements to perform the Shapiro-Wilk test.")

        stat, p_value = shapiro(data)

        # Determine normality based on the p-value
        normality = 'Normal' if p_value >= significance_level else 'Not Normal'

        return {
            'Statistic': stat,
            'p-value': p_value,
            'Normality': normality
        }

    @staticmethod
    def display_shapiro_wilk_results(sw_results:dict, print_output:bool=True, to_html: bool = False):
        # Convert Shapiro-Wilk results to DataFrame
        sw_data = []
        for ticker, values in sw_results.items():
            row = {
                'Ticker': ticker, 
                'Shapiro-Wilk Statistic': values['Statistic'], 
                'p-value': values['p-value'], 
                'Normality': values['Normality']
            }
            sw_data.append(row)

        sw_df = pd.DataFrame(sw_data)
        footnote = "** If p-value < 0.05, then REJECT the Null Hypothesis of normality (i.e., data is not normally distributed).\n"

        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = sw_df.to_html(index=False, border=1)
            html_explanation = f"<p>{footnote}</p>"
            html_output = f"<h2>Shapiro Wilk Results</h2>\n{html_table}\n{html_explanation}"
            return html_output
        elif print_output:
            print(f"Shapiro Wilk Results:\n{sw_df}\n{footnote}")
        else:
            return f"Shapiro Wilk Results:\n{sw_df.to_string(index=False)}\n{footnote}"
    
    @staticmethod
    def histogram_ndc(data:pd.Series, bins='auto', title='Histogram with Normal Distribution Curve'):
        """
        Create a histogram for the given data and overlay a normal distribution fit.

        Args:
        data (array-like): The dataset for which the histogram is to be created.
        bins (int or sequence or str): Specification of bin sizes. Default is 'auto'.
        title (str): Title of the plot.

        Returns:
        matplotlib figure: A histogram with a normal distribution fit.
        """
        # Convert data to a numpy array if it's not already
        data = np.asarray(data)

        # Generate histogram
        plt.figure(figsize=(10, 6))
        sns.histplot(data, bins=bins, kde=False, color='blue', stat="density")

        # Fit and overlay a normal distribution
        mean, std = norm.fit(data)
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        p = norm.pdf(x, mean, std)
        plt.plot(x, p, 'k', linewidth=2)

        title += f'\n Fit Results: Mean = {mean:.2f},  Std. Dev = {std:.2f}'
        plt.title(title)
        plt.xlabel('Value')
        plt.ylabel('Density')

        # Show the plot
        plt.show()

    @staticmethod
    def histogram_kde(data: pd.Series, bins='auto', title='Histogram with Kernel Density Estimate (KDE)'):
        """
        Create a histogram for the given data to visually check for normal distribution.

        Args:
        data (array-like): The dataset for which the histogram is to be created.
        bins (int or sequence or str): Specification of bin sizes. Default is 'auto'.
        title (str): Title of the plot.

        Returns:
        matplotlib figure: A histogram for assessing normality.
        """
        # Convert data to a numpy array if it's not already
        data = np.asarray(data)

        # Generate histogram
        plt.figure(figsize=(10, 6))
        sns.histplot(data, bins=bins, kde=True, color='blue')

        plt.title(title)
        plt.xlabel('Value')
        plt.ylabel('Frequency')

        # Show the plot
        plt.show()
    
    @staticmethod
    def qq_plot(data:pd.Series, title='Q-Q Plot'):
        """
        Create a Q-Q plot for the given data comparing it against a normal distribution.

        Args:
        data (array-like): The dataset for which the Q-Q plot is to be created.
        title (str): Title of the plot.

        Returns:
        matplotlib figure: A Q-Q plot.
        """
        # Convert data to a numpy array if it's not already
        data = np.asarray(data)

        # Generate Q-Q plot
        plt.figure(figsize=(6, 6))
        stats.probplot(data, dist="norm", plot=plt)

        # Add title and labels
        plt.title(title)
        plt.xlabel('Theoretical Quantiles')
        plt.ylabel('Sample Quantiles')

        # Show the plot
        plt.show()
    
    # -- Heteroscedasticity -- 
    @staticmethod
    def breusch_pagan(x:np.array, y:np.array, significance_level:float=0.05):
        """
        Perform the Breusch-Pagan test to assess the presence of heteroscedasticity in a linear regression model.

        Heteroscedasticity occurs when the variance of the residuals is not constant across all levels of the independent
        variables, potentially violating an assumption of linear regression models and affecting inference.

        Args:
            x (np.array): The independent variables (explanatory variables) of the regression model. Should be 2D.
            y (np.array): The dependent variable (response variable) of the regression model. Should be 1D.
            significance_level (float): The significance level at which to test for heteroscedasticity. Default is 0.05.

        Returns:
            dict: A dictionary containing the Breusch-Pagan test statistic ('Breusch-Pagan Test Statistic'),
                the p-value ('p-value'), and an indication of heteroscedasticity ('Heteroscedasticity': 'Present'
                if detected, otherwise 'Absent').

        Raises:
            ValueError: If `x` or `y` are empty, or if their dimensions are incompatible.
        """
        # Add a constant to the independent variables matrix
        X = sm.add_constant(x)

        # Fit the regression model
        model = sm.OLS(y, X).fit()

        # Get the residuals
        residuals = model.resid

        # Perform the Breusch-Pagan test
        bp_test = het_breuschpagan(residuals, model.model.exog)

        # Extract the test statistic and p-value
        bp_test_statistic = bp_test[0]
        bp_test_pvalue = bp_test[1]

        # Prepare the results in a clean format
        output = {
            'Breusch-Pagan Test Statistic': bp_test_statistic,
            'p-value': bp_test_pvalue,
            'Heteroscedasticity': ''
        }

        # Determine heteroscedasticity based on the significance level and p-value
        heteroscedasticity = bp_test_pvalue < significance_level

        output['Heteroscedasticity'] = 'Present' if heteroscedasticity else 'Absent'

        return output

    @staticmethod
    def display_breusch_pagan_results(bp_results:dict, print_output:bool=True, to_html: bool = False):
        # Convert Breusch-Pagan results to DataFrame
        bp_data = []
        for ticker, values in bp_results.items():
            row = {
                'Ticker': ticker,
                'Breusch-Pagan Test Statistic': values['Breusch-Pagan Test Statistic'],
                'p-value': round(values['p-value'], 6),
                'Heteroscedasticity': values['Heteroscedasticity']
            }
            bp_data.append(row)

        bp_df = pd.DataFrame(bp_data)
        footnote = "** IF p-value < 0.05, then REJECT the Null Hypothesis of homoscedasticity (constant variance) in favor of heteroscedasticity (varying variance).\n"
        
        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = bp_df.to_html(index=False, border=1)
            html_explanation = f"<p>{footnote}</p>"
            html_output = f"<h2>Breusch Pagan Results</h2>\n{html_table}\n{html_explanation}"
            return html_output
        elif print_output:
            print(f"Breusch Pagan Results:\n{bp_df}\n{footnote}")
        else:
            return f"Breusch Pagan Results:\n{bp_df.to_string(index=False)}\n{footnote}"
        
    @staticmethod
    def white_test(x: np.array, y: np.array, significance_level: float = 0.05):
        """
        Perform White's test for heteroscedasticity in a linear regression model.

        White's test assesses the null hypothesis that the variance of the residuals in the regression model is homoscedastic
        (constant across levels of the independent variables).

        Args:
            x (np.array): The independent variables of the regression model, excluding the intercept.
                        Should be a 2D array where each column is a variable.
            y (np.array): The dependent variable of the regression model. Should be a 1D array.
            significance_level (float): The significance level for testing heteroscedasticity. Defaults to 0.05.

        Returns:
            dict: A dictionary containing the White test statistic ('White Test Statistic'), the p-value ('p-value'), and
                an indication of heteroscedasticity ('Heteroscedasticity': 'Present' if detected, otherwise 'Absent').

        Raises:
            ValueError: If `x` or `y` are empty, if their dimensions are incompatible, or if `x` is not 2-dimensional.
        """
        if x.size == 0 or y.size == 0:
            raise ValueError("Input arrays x and y must not be empty.")
        if x.ndim != 2:
            raise ValueError("Input array x must be 2-dimensional.")
        if y.ndim != 1:
            raise ValueError("Input array y must be 1-dimensional.")
        
        # Add a constant to the independent variables matrix
        X = sm.add_constant(x)

        # Fit the regression model
        model = sm.OLS(y, X).fit()

        # Perform White's test
        test_statistic, p_value, _, _ = het_white(model.resid, model.model.exog)

        # Determine heteroscedasticity based on the p-value and significance level
        heteroscedasticity = 'Present' if p_value < significance_level else 'Absent'

        return {
            'White Test Statistic': test_statistic,
            'p-value': p_value,
            'Heteroscedasticity': heteroscedasticity
        }

    @staticmethod
    def display_white_test_results(white_results:dict, print_output:bool=True, to_html: bool = False):
        # Convert White test results to DataFrame
        white_data = []
        for ticker, values in white_results.items():
            row = {
                'Ticker': ticker,
                'White Test Statistic': values['White Test Statistic'],
                'p-value': round(values['p-value'], 6),
                'Heteroscedasticity': values['Heteroscedasticity']
            }
            white_data.append(row)

        white_df = pd.DataFrame(white_data)
        footnote = "** IF p-value < 0.05, then REJECT the Null Hypothesis of homoscedasticity (constant variance) in favor of heteroscedasticity (varying variance).\n"

        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = white_df.to_html(index=False, border=1)
            html_explanation = f"<p>{footnote}</p>"
            html_output = f"<h2>White Test Results</h2>\n{html_table}\n{html_explanation}"
            return html_output
        elif print_output:
            print(f"White Test Results:\n{white_df}\n{footnote}")
        else:
            return f"White Test Results:\n{white_df.to_string(index=False)}\n{footnote}"

    # -- Granger Causality -- 
    @staticmethod
    def granger_causality(data: pd.DataFrame, max_lag: int, significance_level: float = 0.05):
        """
        Perform Granger Causality tests to determine if one time series can forecast another.

        This method tests for each pair of variables in the provided DataFrame to see if the past values
        of one variable help to predict the future values of another, indicating a Granger causal relationship.

        Args:
            data (pd.DataFrame): A pandas DataFrame where each column represents a time series variable.
            max_lag (int): The maximum number of lags to test for Granger causality.
            significance_level (float): The significance level for determining statistical significance.

        Returns:
            dict: A dictionary with keys as tuples (cause_variable, effect_variable) and values as dictionaries containing
                the minimum p-value across all tested lags, a boolean indicating Granger causality based on the
                significance level, and the used significance level.

        Raises:
            ValueError: If `data` contains fewer than two columns, as Granger causality requires pairwise comparison.
            ValueError: If `max_lag` is less than 1, as at least one lag is necessary for testing causality.
        """
        if data.shape[1] < 2:
            raise ValueError("DataFrame must contain at least two time series for pairwise Granger causality tests.")
        if max_lag < 1:
            raise ValueError("max_lag must be at least 1.")

        granger_results = {}

        for var1 in data.columns:
            for var2 in data.columns:
                if var1 != var2:
                    test_result = grangercausalitytests(data[[var1, var2]], maxlag=max_lag)
                    p_values = [round(test_result[lag][0]['ssr_chi2test'][1], 4) for lag in range(1, max_lag + 1)]
                    min_p_value = min(p_values)
                    causality = 'Causality' if min_p_value < significance_level else 'Non-Causality'
                    granger_results[(var1, var2)] = {
                        'Min P-Value': min_p_value,
                        'Granger Causality': causality,
                        'Significance Level': significance_level
                    }

        return granger_results

    @staticmethod
    def display_granger_results(granger_results:dict, print_output:bool=True, to_html: bool = False):
        # Creating DataFrame from the results
        granger_df = pd.DataFrame([
            {
                'Variable Pair': f'{pair[0]} -> {pair[1]}',
                'Min p-value': details['min_p_value'],
                'Granger Causality': 'Yes' if details['Granger Causality'] else 'No',
                'Significance Level': details['significance']
            }
            for pair, details in granger_results.items()
        ])

        # Display the DataFrame
        output = f"Granger Causality Results: \n{granger_df}"
        footnote = "** IF p-value < significance level then REJECT the NUll and conclude that the lagged values of one time series can provide useful information for predicting the other time series. \n"

        if to_html:
            # Convert DataFrame to HTML table and add explanation
            html_table = granger_df.to_html(index=False, border=1)
            html_explanation = f"<p>{footnote}</p>"
            html_output = f"<h2>Granger Causality Results</h2>\n{html_table}\n{html_explanation}"
            return html_output
        elif print_output:
            print(f"Granger Causality Results:\n{granger_df}\n{footnote}")
        else:
            return f"Granger Causality Results:\n{granger_df.to_string(index=False)}\n{footnote}"
    

    # -- Historcal Nature --
    @staticmethod
    def rescaled_range_analysis(time_series: np.array, min_chunk_size=8):
        """
        Perform rescaled range analysis on a given time series.

        Parameters:
        - time_series (np.array): The time series data as a NumPy array.
        - min_chunk_size (int): The minimum size of the chunks to start the analysis.

        Returns:
        - np.array: An array of average R/S values for each chunk size.
        """
        N = len(time_series)
        chunk_sizes = [size for size in range(min_chunk_size, N//2 + 1, min_chunk_size)]
        rs_values = []

        for size in chunk_sizes:
            # Creating chunks
            chunks = [time_series[i:i+size] for i in range(0, N, size) if len(time_series[i:i+size]) == size]

            rs_values_for_size = []
            for chunk in chunks:
                # Mean Adjusting
                mean_adjusted_chunk = chunk - np.mean(chunk)

                # Cumulative Deviation
                cumulative_deviation = np.cumsum(mean_adjusted_chunk)

                # Range and Standard Deviation
                R = np.max(cumulative_deviation) - np.min(cumulative_deviation)
                S = np.std(chunk)

                # Calculating R/S and adding to the list for the current chunk size
                if S != 0:
                    rs_values_for_size.append(R / S)
                else:
                    rs_values_for_size.append(0)

            # Averaging R/S values for the current chunk size if any values exist
            if rs_values_for_size:
                avg_rs = np.mean(rs_values_for_size)
                rs_values.append(avg_rs)
            else:
                rs_values.append(0)

        return np.array(rs_values)

    @staticmethod
    def hurst_exponent(time_series, min_chunk_size=8):
        """
        (Adjusted documentation to reflect the use of actual chunk sizes)
        """
        rs_values = TimeseriesTests.rescaled_range_analysis(time_series, min_chunk_size=min_chunk_size)
        
        N = len(time_series)
        chunk_sizes = np.array([size for size in range(min_chunk_size, N//2 + 1, min_chunk_size)])
        log_chunk_sizes = np.log(chunk_sizes)
        log_rs_values = np.log(rs_values)
        
        log_chunk_sizes_with_constant = sm.add_constant(log_chunk_sizes)
        
        model = sm.OLS(log_rs_values, log_chunk_sizes_with_constant)
        results = model.fit()
        
        return results.params[1]  # Hurst exponent
    

    # @staticmethod
    # def hurst_exponent(series: np.array):
    #     # """
    #     # Calculate the Hurst exponent to determine the long-term memory of a time series.

    #     # The Hurst exponent indicates the level of autocorrelation within a time series:
    #     # - A Hurst exponent close to 0.5 suggests a random walk (no autocorrelation).
    #     # - A Hurst exponent greater than 0.5 indicates a positive autocorrelation (trending behavior).
    #     # - A Hurst exponent less than 0.5 suggests a negative autocorrelation (mean-reverting behavior).

    #     # Args:
    #     #     series (np.array): The time series for which to calculate the Hurst exponent.

    #     # Returns:
    #     #     float: The estimated Hurst exponent of the time series.

    #     # Raises:
    #     #     ValueError: If `series` is too short, making it impossible to calculate the exponent accurately.
    #     #     TypeError: If the input `series` is not a NumPy array.
    #     # """

    #     # # Check if the input is a numpy array
    #     # if not isinstance(series, np.ndarray):
    #     #     raise TypeError("Input series must be a NumPy array.")

    #     # if len(series) < 20:
    #     #     raise ValueError("Time series is too short to accurately calculate the Hurst exponent. Length must be at least 100.")
        
    #     # # Define the range of lags
    #     # lags = range(2, 20)

    #     # # Mean-adjust the series
    #     # mean_adjusted_series = series - np.mean(series)
        
    #     # # Calculate the array of the variances of the lagged differences
    #     # tau = []
    #     # for lag in lags:
    #     #     # Calculate lagged differences
    #     #     lagged_diff = np.subtract(mean_adjusted_series[lag:],  mean_adjusted_series[:-lag])
            
    #     #     # Calculate standard deviation of lagged differences
    #     #     std_lagged_diff = np.std(lagged_diff)

    #     #     tau.append(std_lagged_diff)

    #     # # Ensure tau values are positive before taking logs
    #     # tau = [max(t, 1e-10) for t in tau]  # Replace 0s with a small positive value
        
    #     # # Use a linear fit to estimate the Hurst Exponent
    #     # poly = np.polyfit(np.log(lags), np.log(tau), 1)
        
    #     # # The Hurst exponent is the slope of the linear fit times 2
    #     # return poly[0] * 2.0

    #     # Ensure the input is a NumPy array
    #     if not isinstance(series, np.ndarray):
    #         raise TypeError("Input series must be a NumPy array.")
        
    #     N = len(series)
    #     if N < 20:
    #         raise ValueError("Time series is too short to accurately calculate the Hurst exponent. Length must be at least 20.")
        
    #     # Define the maximum size for n to avoid too large segments
    #     max_n = N // 2
    #     lags = range(2, max_n)
    #     RS = []
        
    #     for lag in lags:
    #         # Partition the series into non-overlapping segments of size n
    #         segments = [series[i:i+lag] for i in range(0, N, lag) if len(series[i:i+lag]) == lag]
            
    #         R_over_S = []
    #         for segment in segments:
    #             # Mean Adjusting
    #             mean_adjusted = segment - np.mean(segment)
                
    #             # Cumulative Deviation
    #             cumulative_deviation = np.cumsum(mean_adjusted)
                
    #             # Range
    #             R = np.max(cumulative_deviation) - np.min(cumulative_deviation)
                
    #             # Standard Deviation
    #             S = np.std(segment)
                
    #             # Rescaled Range for the segment
    #             R_over_S.append(R / S)
            
    #         # Average Rescaled Range for the current lag
    #         RS.append(np.mean(R_over_S))

    #         logs = np.log(lags)
    #         logRS = np.log(RS)

    #         # Add a constant to the independent variable to account for the intercept
    #         logs_with_constant = sm.add_constant(logs)

    #         # Perform OLS regression
    #         model = sm.OLS(logRS, logs_with_constant)
    #         results = model.fit()

    #         # The slope (Hurst exponent) and intercept can be retrieved like this
    #         slope = results.params[1]
    #         intercept = results.params[0]

    #         # Now you also have access to a wealth of statistical information
    #         print(results.summary())
        
    #     # Scaling Behavior: Plot log(R/S) against log(n) and perform a linear regression
    #     logs = np.log(lags)
    #     logRS = np.log(RS)
    #     slope, _ = np.polyfit(logs, logRS, 1)
        
    #     # The slope of the linear fit is the estimate of the Hurst exponent
    #     return slope
    
    @staticmethod
    def half_life(Y: pd.Series, Y_lagged: pd.Series, include_constant: bool = True):
        """
        Calculate the expected half-life of a mean-reverting time series using an AR(1) model.

        The half-life is the period over which the deviation from the mean is expected to be halved,
        based on the autoregressive coefficient from the AR(1) model.

        Parameters:
        Y (pd.Series): The dependent variable representing the current values of the time series.
        Y_lagged (pd.Series): The independent variable representing the lagged values of the time series.
        include_constant (bool, optional): Whether to include a constant term in the regression model. Defaults to True.

        Returns:
        float: The half-life of mean reversion, representing how quickly the series reverts to its mean.
        pd.Series: Residuals from the regression model, indicating the error term for each observation.

        Raises:
        ValueError: If the calculated autoregressive coefficient (phi) is outside the expected range (0, 1),
                    indicating that the time series may not exhibit mean-reverting behavior.
        """
        # Check if the series are properly aligned
        if len(Y) != len(Y_lagged):
            raise ValueError("The length of Y and Y_lagged must be the same.")

        if include_constant:
            Y_lagged = sm.add_constant(Y_lagged)  # Add a constant term to the regression model

        model = sm.OLS(Y, Y_lagged).fit()  # Fit the AR(1) model
        
        if model.params.index[0] == 'const':
            phi = model.params.iloc[1]  # If there's a constant, the slope coefficient is the second parameter
        else:
            phi = model.params.iloc[0]  # If there's no constant, the slope coefficient is the first parameter

        # Ensure phi is in the expected range for mean reversion
        if not (0 < phi < 1):
            raise ValueError("Phi is outside the expected range (0, 1). The time series may not be mean-reverting.")

        half_life = -np.log(2) / np.log(phi)  # Calculate the half-life of mean reversion
        residuals = model.resid  # Extract the residuals from the model

        return half_life, residuals
    
        
    # -- VECM Model --
    # !!! Untested!!! 
    @staticmethod
    def vecm_model(data:pd.DataFrame, coint_rank:int, k_ar_diff:int):
        # Estimate the VECM model
        model = VECM(data, k_ar_diff= k_ar_diff, coint_rank=coint_rank)
        fitted_model = model.fit()
        return fitted_model

    # -- Forescast Metrics -- 
    @staticmethod
    def evaluate_forecast(actual: pd.DataFrame, forecast: pd.DataFrame, print_output: bool = True) -> dict:
        """
        Evaluate the accuracy of forecasted values against actual observations using various metrics.

        Args:
            actual (pd.DataFrame or pd.Series): The actual observed values.
            forecast (pd.DataFrame or pd.Series): The forecasted values.
            print_output (bool, optional): Flag indicating whether to print the output. Defaults to True.

        Returns:
            dict: A dictionary of forecast accuracy metrics for each series, including MAE, MSE, RMSE, and MAPE.

        Raises:
            ValueError: If `actual` or `forecast` are not pandas Series or DataFrame.
                        If `actual` and `forecast` have different lengths or indexes.
        """
        if not isinstance(actual, (pd.Series, pd.DataFrame)) or not isinstance(forecast, (pd.Series, pd.DataFrame)):
            raise ValueError("Actual and forecast data must be pandas Series or DataFrame.")
        if actual.shape != forecast.shape:
            raise ValueError("Actual and forecast must have the same shape.")
        if not actual.index.equals(forecast.index):
            raise ValueError("Actual and forecast must have the same index.")

        results = {}
        columns = actual.columns if isinstance(actual, pd.DataFrame) else [actual.name]
        for col in columns:
            ac = actual[col] if isinstance(actual, pd.DataFrame) else actual
            fc = forecast[col] if isinstance(forecast, pd.DataFrame) else forecast
            mae = mean_absolute_error(ac, fc)
            mse = mean_squared_error(ac, fc)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((ac - fc) / ac).replace([np.inf, -np.inf], np.nan)) * 100

            metrics = {'MAE': mae, 'MSE': mse, 'RMSE': rmse, 'MAPE': mape}
            results[col] = metrics

            if print_output:
                print(f"Metrics for {col}:\n{pd.DataFrame([metrics])}\n")

        return results if not print_output else None

    # -- Plots --
    @staticmethod
    def line_plot(x:pd.Series,y:pd.Series, title:str="Time Series Plot", x_label:str="Time",y_label:str="Value"):
        plt.figure(figsize=(10, 6))
        plt.plot(x, y, marker='o')
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.grid(True)
        plt.show()

    @staticmethod
    def plot_forecast(actual:pd.DataFrame, forecast:pd.DataFrame):
        # Ensure actual_values and forecasted_values have the same columns
        if set(actual.columns) != set(forecast.columns):
            raise ValueError("Columns of actual_values and forecasted_values do not match")

        # Iterate over each column to create separate plots
        for column in actual.columns:
            fig, ax = plt.subplots(figsize=(12, 6))

            # Plot the actual values
            ax.plot(actual[column], label=f"{column} Actual", color='blue')

            # Plot the forecasted values
            if column in forecast.columns:
                ax.plot(forecast[column], label=f"{column} Forecast", color='red')

            # Add labels, legend, and grid
            ax.grid(True)
            ax.set_xlabel('Time')
            ax.set_ylabel('Value')
            ax.set_title(f'Actual vs. Forecast for {column}')
            ax.legend()

            # Customize x-axis labels for readability
            plt.xticks(rotation=45)

            # Show the plot
            plt.show()  
    
    @staticmethod
    def plot_price_and_spread(price_data:pd.DataFrame, spread:pd.Series, show_plot=True):
        """
        Plot multiple ticker data on the left y-axis and spread with mean and standard deviations on the right y-axis.
        
        Parameters:
            price_data (pd.DataFrame): DataFrame containing the data with timestamps as index and multiple ticker columns.
            spread (pd.Series): Series containing the spread data.
        """
        # Extract data from the DataFrame
        timestamps = price_data.index

        # Create a figure and primary axis for price data (left y-axis)
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Plot each ticker on the left y-axis
        colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black', 'orange']  # Extend this list as needed
        for i, ticker in enumerate(price_data.columns):
            color = colors[i % len(colors)]  # Cycle through colors
            ax1.plot(timestamps, price_data[ticker], label=ticker, color=color, linewidth=2)

        ax1.set_yscale('linear')
        ax1.set_ylabel('Price')
        ax1.legend(loc='upper left')

        # Calculate mean and standard deviations for spread
        spread_mean = spread.rolling(window=20).mean()  # Adjust the window size as needed
        spread_std_1 = spread.rolling(window=20).std()  # 1 standard deviation
        spread_std_2 = 2 * spread.rolling(window=20).std()  # 2 standard deviations

        # Create a secondary axis for the spread with mean and standard deviations (right y-axis)
        ax2 = ax1.twinx()

        # Plot Spread on the right y-axis
        ax2.plot(timestamps, spread, label='Spread', color='purple', linewidth=2)
        ax2.plot(timestamps, spread_mean, label='Mean', color='orange', linestyle='--')
        ax2.fill_between(timestamps, spread_mean - spread_std_1, spread_mean + spread_std_1, color='gray', alpha=0.2, label='1 Std Dev')
        ax2.fill_between(timestamps, spread_mean - spread_std_2, spread_mean + spread_std_2, color='gray', alpha=0.4, label='2 Std Dev')
        ax2.set_yscale('linear')
        ax2.set_ylabel('Spread and Statistics')
        ax2.legend(loc='upper right')

        # Add grid lines
        ax1.grid(True)

        # Format x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.xlabel('Timestamp')

        # Title
        plt.title('Price Data, Spread, and Statistics Over Time')

        # Show the plot
        plt.tight_layout()
        
        if show_plot:
            plt.show()

    @staticmethod
    def plot_zscore(zscore_series:pd.Series, window=20):
        """
        Plot Z-score along with its mean and standard deviations (1 and 2) on the right y-axis.
        
        Parameters:
            zscore_series (pd.Series): Series containing the Z-score data.
            window (int): Rolling window size for calculating mean and standard deviations (default is 20).
        """
        # Create a figure and primary axis for Z-score (left y-axis)
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Plot Z-score on the left y-axis
        ax1.plot(zscore_series.index, zscore_series, label='Z-Score', color='blue', linewidth=2)

        ax1.set_yscale('linear')
        ax1.set_ylabel('Z-Score')
        ax1.legend(loc='upper left')

        # Calculate mean and standard deviations for Z-score
        zscore_mean = zscore_series.rolling(window=window).mean()
        zscore_std_1 = zscore_series.rolling(window=window).std()  # 1 standard deviation
        zscore_std_2 = 2 * zscore_series.rolling(window=window).std()  # 2 standard deviations

        # Create a secondary axis for mean and standard deviations (right y-axis)
        ax2 = ax1.twinx()

        # Plot mean and standard deviations on the right y-axis
        ax2.plot(zscore_series.index, zscore_mean, label='Mean', color='orange', linestyle='--')
        ax2.fill_between(zscore_series.index, zscore_mean - zscore_std_1, zscore_mean + zscore_std_1, color='gray', alpha=0.2, label='1 Std Dev')
        ax2.fill_between(zscore_series.index, zscore_mean - zscore_std_2, zscore_mean + zscore_std_2, color='gray', alpha=0.4, label='2 Std Dev')
        ax2.set_yscale('linear')
        ax2.set_ylabel('Statistics')
        ax2.legend(loc='upper right')

        # Add grid lines
        ax1.grid(True)

        # Format x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.xlabel('Timestamp')

        # Title
        plt.title('Z-Score and Statistics Over Time')

        # Show the plot
        plt.tight_layout()
        plt.show()

    # Function to fit models and compare
    @staticmethod
    def fit_and_compare(self, time, values):
        # Fit linear model
        params_linear, _ = curve_fit(self._linear_model, time, values)

        # Fit log-transformed exponential model
        log_values = np.log(values)
        params_log_exp, _ = curve_fit(self._log_exponential_model, time, log_values)

        # Compute residuals
        residuals_linear = values - self._linear_model(time, *params_linear)
        residuals_log_exp = log_values - self._log_exponential_model(time, *params_log_exp)

        # Plotting
        plt.figure(figsize=(12, 6))

        # Linear Fit
        plt.subplot(1, 2, 1)
        plt.plot(time, values, 'o', label="Data")
        plt.plot(time, self._linear_model(time, *params_linear), label="Linear Fit")
        plt.title("Linear Fit")
        plt.legend()

        # Log-Transformed Exponential Fit
        plt.subplot(1, 2, 2)
        plt.plot(time, values, 'o', label="Data")
        plt.plot(time, np.exp(self._log_exponential_model(time, *params_log_exp)), label="Exponential Fit")
        plt.title("Exponential Fit")
        plt.legend()

        plt.show()

        return residuals_linear, np.exp(residuals_log_exp) - values
   
    # Linear model -- Untested
    @staticmethod
    def _linear_model(self, t, a, b):
        return a + b * t

    # Exponential model
    @staticmethod
    def _exponential_model(self, t, a, b):
        return a * np.exp(b * t)

    # Log-transformed exponential model
    @staticmethod
    def _log_exponential_model(self, t, log_a, b):
        return log_a + b * t
   
    # @staticmethod
    # def plot_price_and_spread_w_signals(price_data: pd.DataFrame, spread: pd.Series, signals: list, split_date=None, show_plot=True):
    #     """
    #     Plot multiple ticker data on the left y-axis, spread with mean and standard deviations on the right y-axis,
    #     and trading signals as icons.
        
    #     Parameters:
    #         price_data (pd.DataFrame): DataFrame containing the data with timestamps as index and multiple ticker columns.
    #         spread (pd.Series): Series containing the spread data.
    #         signals (pd.DataFrame): DataFrame containing signal data with timestamps as index and 'signal' column indicating 'long' or 'short'.
    #     """
    #     # Extract data from the DataFrame
    #     timestamps = price_data.index

    #     # Create a figure and primary axis for price data (left y-axis)
    #     fig, ax1 = plt.subplots(figsize=(12, 6))

    #     # Plot each ticker on the left y-axis
    #     colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black', 'orange']  # Extend this list as needed
    #     for i, ticker in enumerate(price_data.columns):
    #         color = colors[i % len(colors)]  # Cycle through colors
    #         ax1.plot(timestamps, price_data[ticker], label=ticker, color=color, linewidth=2)

    #     ax1.set_yscale('linear')
    #     ax1.set_ylabel('Price')
    #     ax1.legend(loc='upper left')

    #     # Calculate mean and standard deviations for spread
    #     spread_mean = spread.rolling(window=20).mean()  # Adjust the window size as needed
    #     spread_std_1 = spread.rolling(window=20).std()  # 1 standard deviation
    #     spread_std_2 = 2 * spread.rolling(window=20).std()  # 2 standard deviations

    #     # Create a secondary axis for the spread with mean and standard deviations (right y-axis)
    #     ax2 = ax1.twinx()

    #     # Plot Spread on the right y-axis
    #     ax2.plot(timestamps, spread, label='Spread', color='purple', linewidth=2)
    #     ax2.plot(timestamps, spread_mean, label='Mean', color='orange', linestyle='--')
    #     ax2.fill_between(timestamps, spread_mean - spread_std_1, spread_mean + spread_std_1, color='gray', alpha=0.2, label='1 Std Dev')
    #     ax2.fill_between(timestamps, spread_mean - spread_std_2, spread_mean + spread_std_2, color='gray', alpha=0.4, label='2 Std Dev')
    #     ax2.set_yscale('linear')
    #     ax2.set_ylabel('Spread and Statistics')
    #     ax2.legend(loc='upper right')

    #     # Plot signals
    #     for signal in signals:
    #         ts = pd.to_datetime(signal['timestamp'])
    #         price = signal['price']
    #         action = signal['action']
    #         if action == 'long':
    #             marker = '^'
    #             color = 'lime'
    #         elif action == 'short':
    #             marker = 'v'
    #             color = 'red'
    #         else:
    #             # Default marker for undefined actions
    #             marker = 'o'
    #             color = 'gray'
    #         ax1.scatter(ts, price, marker=marker, color=color, s=100)

    #     # Draw a dashed vertical line to separate test and training data
    #     if split_date is not None:
    #         split_date = pd.to_datetime(split_date)
    #         ax1.axvline(x=split_date, color='black', linestyle='--', linewidth=1)

    #     # Add grid lines
    #     ax1.grid(True)

    #     # Format x-axis labels for better readability
    #     plt.xticks(rotation=45)
    #     plt.xlabel('Timestamp')

    #     # Title
    #     plt.title('Price Data, Spread, Statistics, and Trading Signals Over Time')

    #     # Show the plot
    #     plt.tight_layout()
        
    #     if show_plot:
    #         plt.show()

 
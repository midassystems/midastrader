
import numpy as np
import pandas as pd
from typing import List
from decimal import Decimal
import statsmodels.api as sm

class RegressionAnalysis:
    def __init__(self, strategy_values: pd.DataFrame, benchmark_values: pd.DataFrame, risk_free_rate=0.01):
        """
        Initializes the RegressionAnalysis with strategy and benchmark returns.
        """
        self.model = None
        self.risk_free_rate = risk_free_rate
        self.equity_curve = strategy_values['equity_value']
        self.strategy_returns, self.benchmark_returns = self._prepare_and_align_data(strategy_values, benchmark_values)

    # Data pre-processing
    def _standardize_to_daily_values(self, data: pd.DataFrame, value_column: str) -> pd.DataFrame:
        """
        Converts input DataFrame to daily frequency, based on the 'timestamp' column,
        and calculates daily returns of the 'value_column'.
        """
        # Ensure 'timestamp' column is datetime type and set as index
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.set_index('timestamp', inplace=True)
        
        # Resample to daily frequency, taking the last value of the day
        daily_data = data.resample('D').last()

        # Drop rows with any NaN values that might have resulted from resampling
        daily_data.dropna(inplace=True)

        # Calculate daily returns
        daily_returns = daily_data[value_column].pct_change().dropna()

        return daily_returns
    
    def _prepare_and_align_data(self, strategy_curve: pd.DataFrame, benchmark_curve: pd.DataFrame):
        """
        Aligns strategy and benchmark data on a common date index and calculates returns.
        Assumes 'equity_curve' column in strategy_curve and 'close' column in benchmark_curve.
        """
        strategy_returns = self._standardize_to_daily_values(strategy_curve, 'equity_value')
        benchmark_returns = self._standardize_to_daily_values(benchmark_curve, 'close')

        # Align the two datasets, keeping only the dates that exist in both
        aligned_returns = pd.concat([strategy_returns, benchmark_returns], axis=1, join='inner').dropna()

        return aligned_returns.iloc[:, 0], aligned_returns.iloc[:, 1]

    # Regression Model
    def perform_regression_analysis(self):
        """
        Performs a simple linear regression between strategy returns and benchmark returns.
        """
        X = sm.add_constant(self.benchmark_returns)
        model = sm.OLS(self.strategy_returns, X).fit()
        self.model = model
        return model.summary()
    
    def validate_model(self, r_squared_threshold=0.02, p_value_threshold=0.05):
        """
        Validates the regression model based on R-squared and p-values significance.
        """
        if not self.model:
            print("Regression analysis not performed yet.")
            return None

        # Validation criteria checks
        is_valid_r_squared = self.model.rsquared > r_squared_threshold
        is_valid_p_values = all(p < p_value_threshold for p in self.model.pvalues[1:])

        validation_results = {
            "R-squared": self.model.rsquared,
            "P-values": self.model.pvalues.to_dict(),
            "Validation Checks": {
                "R-squared above threshold": is_valid_r_squared,
                "P-values significant": is_valid_p_values,
                "Model is valid": is_valid_r_squared and is_valid_p_values
            }
        }

        return validation_results

    # Regression Analysis
    def beta(self) -> float:
        """
        Calculates the beta of the strategy based on aligned strategy and benchmark returns.
        """
        if self.model is None:
            raise ValueError("Regression model not fitted. Call perform_regression_analysis first.")

        # The beta is the coefficient of the benchmark returns in the regression model.
        beta_value = self.model.params.iloc[1]  # Assuming 'params[1]' is the beta coefficient
        return round(beta_value, 4)

    def alpha(self) -> float:
        """
        Calculates the alpha of the strategy based on aligned strategy and benchmark returns.
        """
        if self.model is None:
            raise ValueError("Regression model not fitted. Call perform_regression_analysis first.")
        
        # Annualizing the returns
        annualized_strategy_return = np.mean(self.strategy_returns) * 252
        annualized_benchmark_return = np.mean(self.benchmark_returns) * 252
        
        beta_value = self.beta()
        
        # The alpha can be calculated as the intercept in the regression model.
        alpha_value = annualized_strategy_return - (self.risk_free_rate + beta_value * (annualized_benchmark_return - self.risk_free_rate))
        
        return round(alpha_value, 4)
    
    def analyze_alpha(self, p_value_threshold=0.05):
        """
        Analyzes the significance of alpha (intercept) in the regression model.
        """
        if not self.model:
            print("Regression analysis not performed yet.")
            return None

        # Extract alpha (intercept) p-value and confidence interval
        p_value_alpha = self.model.pvalues['const']
        conf_interval_alpha = self.model.conf_int().loc['const'].values

        # Assess significance
        is_alpha_significant = p_value_alpha < p_value_threshold
        does_alpha_span_zero = conf_interval_alpha[0] < 0 < conf_interval_alpha[1]

        alpha_analysis_results = {
            "Alpha (Intercept)": self.model.params['const'],
            "P-value": p_value_alpha,
            "Confidence Interval": conf_interval_alpha.tolist(),
            "Alpha is significant": is_alpha_significant,
            "Confidence Interval spans zero": does_alpha_span_zero
        }

        return alpha_analysis_results

    def analyze_beta(self, p_value_threshold=0.05):
        """
        Analyzes the significance of beta (slope) in the regression model.
        """
        if not self.model:
            print("Regression analysis not performed yet.")
            return None

        # Assuming beta is the first variable after the constant in the regression model
        beta = self.model.params.iloc[1]
        p_value_beta = self.model.pvalues.iloc[1]
        conf_interval_beta = self.model.conf_int().iloc[1].values

        # Assess significance
        is_beta_significant = p_value_beta < p_value_threshold
        does_beta_span_one = conf_interval_beta[0] < 1 < conf_interval_beta[1]

        beta_analysis_results = {
            "Beta (Slope)": beta,
            "P-value": p_value_beta,
            "Confidence Interval": conf_interval_beta.tolist(),
            "Beta is significant": is_beta_significant,
            "Confidence Interval spans one": does_beta_span_one
        }

        return beta_analysis_results

    # Measure Risk
    def calculate_volatility_and_zscore_annualized(self):
        """
        Calculates the strategy's annualized volatility and z-scores for 1, 2, and 3 standard deviation moves.
        """
        daily_volatility = self.strategy_returns.std()
        daily_mean_return = self.strategy_returns.mean()
        
        # Annualizing the daily volatility and mean return
        annualized_volatility = daily_volatility * np.sqrt(252)
        annualized_mean_return = daily_mean_return * 252
        
        # Adjusting the calculation of z-scores for annualized values
        z_scores_annualized = {f"Z-score for {x} SD move (annualized)": (annualized_mean_return - x * annualized_volatility) / annualized_volatility for x in range(1, 4)}
        return {
            "Annualized Volatility": annualized_volatility,
            "Annualized Mean Return": annualized_mean_return,
            "Z-Scores (Annualized)": z_scores_annualized
        }

    def risk_decomposition(self):
        """
        Decomposes risk into idiosyncratic, market, and total based on regression analysis.
        """
        if self.model is None:
            self.perform_regression_analysis()
        
        beta = self.model.params.iloc[1]
        market_volatility = self.benchmark_returns.std() * beta
        idiosyncratic_volatility = self.model.resid.std()
        total_volatility = np.sqrt(market_volatility**2 + idiosyncratic_volatility**2)
        
        return {
            "Market Volatility": market_volatility,
            "Idiosyncratic Volatility": idiosyncratic_volatility,
            "Total Volatility": total_volatility
        }

    def performance_attribution(self):
        """
        Attributes performance into idiosyncratic, market, and total.
        """
        if self.model is None:
            self.perform_regression_analysis()
        
        alpha = self.model.params.iloc[0]
        beta = self.model.params.iloc[1]
        market_contrib = beta * self.benchmark_returns.mean()
        idiosyncratic_contrib = alpha
        total_contrib = market_contrib + idiosyncratic_contrib
        
        return {
            "Market Contribution": market_contrib,
            "Idiosyncratic Contribution": idiosyncratic_contrib,
            "Total Contribution": total_contrib
        }

    def calculate_sharpe_ratio(self, risk_free_rate=0.04):
        """
        Calculates the Sharpe ratio of the strategy.
        """
        excess_returns = self.strategy_returns - risk_free_rate
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)  # Assuming 252 trading days in a year
        
        return {
            "sharpe_ratio": sharpe_ratio,
            "annualized_return": excess_returns.mean() * 252,
            "annualized_volatility": excess_returns.std() * np.sqrt(252),
            "risk_free_rate": risk_free_rate
        }

    def hedge_analysis(self):
        """
        Calculates portfolio dollar beta, market hedge NMV (Net Market Value), and other portfolio metrics 
        based on a more realistic calculation method, using the stored equity curve.
        """
        if not self.model:
            print("Regression analysis not performed yet.")
            return None

        # Using the last value of the equity curve to represent the current portfolio value
        portfolio_value = self.equity_curve.iloc[-1]
        
        # Assuming self.model.params['beta'] exists and represents the portfolio's beta relative to the market
        beta = self.model.params.iloc[1]
        
        # Calculate portfolio dollar beta
        portfolio_dollar_beta = portfolio_value * beta
        
        # Market Hedge NMV calculation
        market_hedge_nmv = -portfolio_dollar_beta

        return {
            "Portfolio Dollar Beta": portfolio_dollar_beta,
            "Market Hedge NMV": market_hedge_nmv,
            "Beta": beta,
        }

    # Results
    def compile_results(self):
        """
        Compiles the regression analysis results into a dictionary format suitable for input into the Django model.
        """
        if self.model is None:
            raise ValueError("Regression model not fitted. Call perform_regression_analysis first.")

        # Assuming other methods have been called as needed to populate these attributes
        results_dict = {
            "r_squared": str(round(self.model.rsquared, 4)),
            "p_value_alpha" :str(round(self.model.pvalues['const'], 4)),
            "p_value_beta": str(round(self.model.pvalues.iloc[1], 4)),
            "risk_free_rate": str(round(self.risk_free_rate,4)),
            "alpha": str(round(self.alpha(), 4)),
            "beta": str(round(self.beta(),4)),
            "sharpe_ratio": str(round(self.calculate_sharpe_ratio(self.risk_free_rate)["sharpe_ratio"], 4)),
            "annualized_return": str(round(self.calculate_sharpe_ratio(self.risk_free_rate)["annualized_return"], 4)),
            "market_contribution": str(round(self.performance_attribution()["Market Contribution"], 4)),
            "idiosyncratic_contribution": str(round(self.performance_attribution()["Idiosyncratic Contribution"],4)),
            "total_contribution": str(round(self.performance_attribution()["Total Contribution"], 4)),
            "annualized_volatility": str(round(self.calculate_sharpe_ratio(self.risk_free_rate)["annualized_volatility"], 4)),
            "market_volatility": str(round(self.risk_decomposition()["Market Volatility"], 4)),
            "idiosyncratic_volatility": str(round(self.risk_decomposition()["Idiosyncratic Volatility"], 4)),
            "total_volatility": str(round(self.risk_decomposition()["Total Volatility"], 4)),
            "portfolio_dollar_beta": str(round(self.hedge_analysis()["Portfolio Dollar Beta"], 4)),
            "market_hedge_nmv": str(round(self.hedge_analysis()["Market Hedge NMV"], 4))
        }

        return results_dict

from dataclasses import dataclass

@dataclass
class RegressionResults:
    backtest:int
    risk_free_rate:float
    r_squared:float
    adj_r_squared:float
    RMSE:float
    MAE:float
    f_statistic:float
    f_statistic_p_value:float
    durbin_watson:float
    jarque_bera:float
    jarque_bera_p_value:float
    condition_number:float
    alpha:float
    p_value_alpha:float
    total_contribution:float
    systematic_contribution:float
    idiosyncratic_contribution:float
    total_volatility:float
    systematic_volatility:float
    idiosyncratic_volatility:float
    vif:dict 
    beta:dict
    p_value_beta:dict
    timeseries_data:list

    def __post_init__(self):
        if not isinstance(self.vif, dict):
            raise ValueError("'vif' field must be a dictionary.")
        if not isinstance(self.beta, dict):
            raise ValueError("'beta' field must be a dictionary.")
        if not isinstance(self.p_value_beta, dict):
            raise ValueError("'p_value_beta' field must be a dictionary.")
        if not isinstance(self.timeseries_data, list):
            raise ValueError("'timeseries_data' field must be a list.")
        if not isinstance(self.backtest, int):
            raise ValueError("'backtest' field must be an integer.")
        for attr in ['risk_free_rate', 'r_squared', 'adj_r_squared', 'RMSE', 'MAE', 'f_statistic', 
                     'f_statistic_p_value', 'durbin_watson', 'jarque_bera', 'jarque_bera_p_value', 
                     'condition_number', 'alpha', 'p_value_alpha', 'total_contribution', 
                     'systematic_contribution', 'idiosyncratic_contribution', 'total_volatility', 
                     'systematic_volatility', 'idiosyncratic_volatility']:
            if not isinstance(getattr(self, attr), float):
                raise ValueError(f"'{attr}' field must be a float.")
        
    def to_dict(self):
        return {
            "backtest": self.backtest,
            "risk_free_rate": self.risk_free_rate,
            "r_squared": self.r_squared,
            "adjusted_r_squared": self.adj_r_squared,
            "RMSE": self.RMSE,
            "MAE": self.MAE,
            "f_statistic": self.f_statistic,
            "f_statistic_p_value": self.f_statistic_p_value,
            "durbin_watson": self.durbin_watson,
            "jarque_bera": self.jarque_bera,
            "jarque_bera_p_value": self.jarque_bera_p_value,
            "condition_number": self.condition_number,
            "vif": self.vif,
            "alpha": self.alpha,
            "p_value_alpha": self.p_value_alpha,
            "beta": self.beta,
            "p_value_beta": self.p_value_beta,
            "total_contribution": self.total_contribution,
            "systematic_contribution": self.systematic_contribution,
            "idiosyncratic_contribution": self.idiosyncratic_contribution,
            "total_volatility": self.total_volatility,
            "systematic_volatility": self.systematic_volatility,
            "idiosyncratic_volatility": self.idiosyncratic_volatility,
            "timeseries_data": self.timeseries_data
        }

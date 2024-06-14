# user_script.py
from midas.engine.command.main import run
from decouple import config


DATABASE_KEY = config('MIDAS_API_KEY')
DATABASE_URL = config('MIDAS_URL')

# if __name__ == "__main__":
def main():
    run(
        mode="BACKTEST",
        strategy_module="/Users/anthony/git-projects/midas/midasPython/tests/engine_integration/backtest/logic.py",
        strategy_class="Cointegrationzscore",
        # risk_module="/Users/anthony/git-projects/midas/midasPython/tests/engine_integration/backtest/logic.py",
        # risk_class="Cointegrationzscore",
        session_id=1001,
        config_file="/Users/anthony/git-projects/midas/midasPython/tests/engine_integration/backtest/config.json",
        database_key=DATABASE_KEY,
        database_url=DATABASE_URL,
        log_output="file",
        output_path="/Users/anthony/git-projects/midas/midasPython/tests/engine_integration/backtest/output/",
        log_level="INFO"
    )

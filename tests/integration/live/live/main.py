# user_script.py
from midas.engine.command.main import run
from decouple import config

DATABASE_KEY = config("MIDAS_API_KEY")
DATABASE_URL = config("MIDAS_URL")


# if __name__ == "__main__":
def main():
    run(
        mode="LIVE",
        session_id=2009999,
        strategy_class="Cointegrationzscore",
        strategy_module="/Users/anthony/git-projects/midas/midasPython/tests/integration/live/live/logic.py",
        config_file="/Users/anthony/git-projects/midas/midasPython/tests/integration/live/live/config.json",
        database_key=DATABASE_KEY,
        database_url=DATABASE_URL,
        log_output="file",
        output_path="/Users/anthony/git-projects/midas/midasPython/tests/integration/live/output/",
        log_level="INFO",
        # risk_class="Cointegrationzscore",
        # risk_module="/Users/anthony/git-projects/midas/midasPython/tests/engine_integration/live/logic.py",
    )

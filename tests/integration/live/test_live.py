import unittest
from midastrader.cli import run


class MidasLiveIntegration(unittest.TestCase):
    def test_live(self):
        run("tests/integration/strategy/config.toml", "live")


if __name__ == "__main__":
    unittest.main()

import unittest
from midas.cli import run


class MidasLiveIntegration(unittest.TestCase):
    def test_live(self):
        run("tests/integration/strategy/config.toml")


if __name__ == "__main__":
    unittest.main()

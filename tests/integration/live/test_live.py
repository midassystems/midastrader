import unittest

from live.main import main


class MidasLiveIntegration(unittest.TestCase):
    def test_live(self):
        main()  # run full live


if __name__ == "__main__":
    unittest.main()


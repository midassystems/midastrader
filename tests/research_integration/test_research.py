import unittest
from tests.research_integration.research_test.main import main


class MidasResearchIntegration(unittest.TestCase):
    def test_research(self):
        main()
    
if __name__ == "__main__":
    unittest.main()
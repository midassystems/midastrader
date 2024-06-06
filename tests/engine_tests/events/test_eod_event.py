import unittest
from datetime import datetime

from midas.engine.events import EODEvent

# TOOO : edge cases
class TestExecutionEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timetamp = datetime(2024,10, 1)

    # Basic Validation
    def test_valid_construction(self):
        # Test
        event = EODEvent(timestamp=self.valid_timetamp)
        
        # Validate
        self.assertEqual(event.timestamp, self.valid_timetamp)
        self.assertEqual(event.type,"END-OF-DAY")

if __name__=="__main__":
    unittest.main()
import random
import unittest

from midas.events import EODEvent
# TOOO : edge cases
class TestExecutionEvent(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_timetamp = 1651500000

    # Basic Validation
    def test_valid_construction(self):
        # Test
        event = EODEvent(timestamp=self.valid_timetamp)
        
        # Validate
        self.assertEqual(event.timestamp, self.valid_timetamp)
        self.assertEqual(event.type,"End-of-day")

if __name__=="__main__":
    unittest.main()
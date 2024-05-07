import os
import unittest
import pandas as pd
from matplotlib import pyplot as plt
from unittest.mock import patch, mock_open, Mock

from midas.research.report import HTMLReportGenerator

def simple_plot():
    plt.plot([1, 2, 3], [4, 5, 6])

class TestHTMLReportGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.report = HTMLReportGenerator("test_report")
        self.file_path = self.report.file_path

    def tearDown(self):
        """Tear down test fixtures."""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_add_section_title(self):
        # test
        self.report.add_section_title("Test Title")
        
        # validate
        self.assertIn("<h2>Test Title</h2>", self.report.html_content)

    def test_add_list(self):
        summary_dict = {"key1": "value1", "key2": "value2"}
        # test 
        self.report.add_list(summary_dict)
        # validate
        self.assertIn("<li><strong>key1:</strong> value1</li>", self.report.html_content)
        self.assertIn("<li><strong>key2:</strong> value2</li>", self.report.html_content)

    def test_add_image(self):
        # test
        self.report.add_image(simple_plot)
        # validate
        self.assertIn('<img src="data:image/png;base64,', self.report.html_content)

    def test_add_table(self):
        headers = ["Column1", "Column2"]
        rows = [["Row1Cell1", "Row1Cell2"], ["Row2Cell1", "Row2Cell2"]]
        # test 
        self.report.add_table(headers, rows)
        # validate
        self.assertIn("<th>Column1</th>", self.report.html_content)
        self.assertIn("<td>Row1Cell1</td>", self.report.html_content)

    def test_add_dataframe(self):
        df = pd.DataFrame({'Column1': [1, 2], 'Column2': [3, 4]})
        # test
        self.report.add_dataframe(df, "DataFrame Title")
        # validate
        self.assertIn("<h2>DataFrame Title</h2>", self.report.html_content)
        self.assertIn("Column1", self.report.html_content)
        self.assertIn("1", self.report.html_content)

    def test_complete_report(self):
        # Setup
        mock_html_content = "<html><body>Report content</body></html>"
        self.report.html_content = mock_html_content  # Assuming self.report is an instance of the class with complete_report method
        
        # Mock the open function and simulate writing to a file
        with patch("builtins.open", mock_open()) as mocked_file:
            # test
            self.report.complete_report()
            
            # validate
            # Check that open was called correctly with the file path and write mode
            mocked_file.assert_called_with(self.report.file_path, "w")
            
            # Check that write was called with the correct content
            mocked_file().write.assert_called_with(mock_html_content + "</body>\n</html>")


if __name__ =="__main__":
    unittest.main()
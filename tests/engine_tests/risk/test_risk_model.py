import unittest
from unittest.mock import Mock, patch, MagicMock
from midas.engine.risk import BaseRiskModel, load_risk_class


class TestRiskModel(BaseRiskModel):
    def evaluate_risk(self, data: dict) -> dict:
        pass 

class TestLoadStrategyClass(unittest.TestCase):
    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_risk_class_success(self, mock_module_from_spec, mock_spec_from_file_location):
        # Mock module and class
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_module = MagicMock()
        mock_module.TestRiskModel = TestRiskModel
        mock_module_from_spec.return_value = mock_module

        # Test
        strategy_class = load_risk_class('fake/path/to/module.py', 'TestRiskModel')

        # Validate
        self.assertEqual(strategy_class, TestRiskModel)

    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_risk_class_class_not_found(self, mock_module_from_spec, mock_spec_from_file_location):
        # Mock module without the class
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_module = MagicMock()
        mock_module_from_spec.return_value = mock_module

        # Test
        with self.assertRaises(TypeError):
            load_risk_class('fake/path/to/module.py',"BaseStrategy")

    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_risk_class_not_subclass(self, mock_module_from_spec, mock_spec_from_file_location):
        # Mock module with class that is not a subclass of BaseStrategy
        class NotRiskModel:
            pass

        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_module = MagicMock()
        mock_module.NotRiskModel = NotRiskModel
        mock_module_from_spec.return_value = mock_module

        # Test
        with self.assertRaises(ValueError):
            load_risk_class('fake/path/to/module.py', 'NotRiskModel')

    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_risk_class_invalid_module_path(self, mock_module_from_spec, mock_spec_from_file_location):
        # Simulate an ImportError when trying to load the module
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file_location.return_value = mock_spec
        mock_spec.loader.exec_module.side_effect = ImportError("Cannot load module")

        # Test
        with self.assertRaises(ImportError):
            load_risk_class('invalid/path/to/module.py', 'TestRiskModel')


if __name__ == "__main__":
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
from src.retry import retry_on_exception
import logging

class TestRetryDecorator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    @patch('time.sleep')
    def test_retry_on_exception(self, mock_sleep):
        mock_func = MagicMock()
        mock_func.side_effect = [ValueError("test error"), ValueError("test error"), "success"]
        
        decorated_func = retry_on_exception(ValueError, max_retries=3)(mock_func)
        result = decorated_func()

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('time.sleep')
    def test_retry_exceeds_max_retries(self, mock_sleep):
        mock_func = MagicMock()
        mock_func.side_effect = ValueError("test error")
        
        decorated_func = retry_on_exception(ValueError, max_retries=3)(mock_func)
        
        with self.assertRaises(ValueError):
            decorated_func()
        
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('time.sleep')
    def test_should_retry_logic(self, mock_sleep):
        mock_func = MagicMock()
        mock_func.side_effect = [ValueError("retry"), ValueError("don't retry"), "success"]
        
        def should_retry(e):
            return str(e) == "retry"

        decorated_func = retry_on_exception(ValueError, should_retry=should_retry)(mock_func)
        
        with self.assertRaises(ValueError):
            decorated_func()
            
        self.assertEqual(mock_func.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

if __name__ == '__main__':
    unittest.main()

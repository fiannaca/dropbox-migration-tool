import unittest
from unittest.mock import patch, mock_open
import json
import logging
from src.dropbox_auth import get_access_token, save_credentials, load_credentials

class TestDropboxAuth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    @patch('builtins.input', return_value='test_auth_code')
    @patch('webbrowser.open')
    @patch('dropbox.DropboxOAuth2FlowNoRedirect')
    def test_get_access_token_success(self, MockFlow, mock_webbrowser, mock_input):
        mock_flow_instance = MockFlow.return_value
        mock_flow_instance.start.return_value = 'https://dropbox.com/oauth2/authorize'
        mock_oauth_result = mock_flow_instance.finish.return_value
        mock_oauth_result.access_token = 'test_token'

        token = get_access_token('test_app_key', 'test_app_secret')
        self.assertEqual(token, 'test_token')

    @patch('builtins.input', return_value='test_auth_code')
    @patch('webbrowser.open')
    @patch('dropbox.DropboxOAuth2FlowNoRedirect')
    def test_get_access_token_failure(self, MockFlow, mock_webbrowser, mock_input):
        mock_flow_instance = MockFlow.return_value
        mock_flow_instance.start.return_value = 'https://dropbox.com/oauth2/authorize'
        mock_flow_instance.finish.side_effect = Exception('Test Error')

        token = get_access_token('test_app_key', 'test_app_secret')
        self.assertIsNone(token)

    def test_save_and_load_credentials(self):
        m = mock_open()
        with patch('builtins.open', m):
            save_credentials('test_token', 'test_credentials.json')
        
        m.assert_called_once_with('test_credentials.json', 'w')
        handle = m()
        
        # Get all the write calls and join them
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertEqual(written_data, json.dumps({'access_token': 'test_token'}))

        m = mock_open(read_data='{"access_token": "test_token"}')
        with patch('builtins.open', m):
            token = load_credentials('test_credentials.json')
            self.assertEqual(token, 'test_token')
    
    def test_load_credentials_file_not_found(self):
        m = mock_open()
        m.side_effect = FileNotFoundError
        with patch('builtins.open', m):
            token = load_credentials('non_existent_file.json')
            self.assertIsNone(token)

if __name__ == '__main__':
    unittest.main()

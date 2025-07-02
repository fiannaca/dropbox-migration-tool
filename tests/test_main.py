import unittest
from unittest.mock import patch
from src.main import main, get_config
import logging

class TestConfig(unittest.TestCase):
    @patch('os.environ.get')
    @patch('configparser.ConfigParser.read')
    @patch('configparser.ConfigParser.get')
    def test_get_config_from_file(self, mock_config_get, mock_config_read, mock_env_get):
        mock_env_get.return_value = None
        mock_config_get.side_effect = ['test_key_file', 'test_secret_file']
        
        key, secret = get_config()
        self.assertEqual(key, 'test_key_file')
        self.assertEqual(secret, 'test_secret_file')

    @patch('os.environ.get')
    @patch('configparser.ConfigParser.read')
    def test_get_config_from_env(self, mock_config_read, mock_env_get):
        mock_env_get.side_effect = ['test_key_env', 'test_secret_env']
        
        key, secret = get_config()
        self.assertEqual(key, 'test_key_env')
        self.assertEqual(secret, 'test_secret_env')

    @patch('os.environ.get')
    @patch('configparser.ConfigParser.read')
    @patch('configparser.ConfigParser.get')
    def test_get_config_env_overrides_file(self, mock_config_get, mock_config_read, mock_env_get):
        mock_env_get.side_effect = ['test_key_env', 'test_secret_env']
        mock_config_get.side_effect = ['test_key_file', 'test_secret_file']

        key, secret = get_config()
        self.assertEqual(key, 'test_key_env')
        self.assertEqual(secret, 'test_secret_env')

class TestMain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('src.main.Migration')
    def test_main_success(self, MockMigration, mock_get_google_credentials, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        mock_load_dropbox_credentials.return_value = 'test_token'
        main([])
        mock_setup_logger.assert_called_once()
        MockMigration.assert_called_once()

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_dropbox_token')
    @patch('src.main.save_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('src.main.Migration')
    def test_main_new_dropbox_token_with_test_run(self, MockMigration, mock_get_google_credentials, mock_save_dropbox_credentials, mock_get_dropbox_token, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        mock_load_dropbox_credentials.return_value = None
        mock_get_dropbox_token.return_value = 'new_token'
        main(['--test_run'])
        mock_setup_logger.assert_called_once()
        mock_save_dropbox_credentials.assert_called_once_with('new_token')
        MockMigration.assert_called_once()

    def test_main_mutually_exclusive_flags(self):
        with self.assertRaises(SystemExit):
            main(['--test_run', '--interactive'])

    @patch('src.main.get_config', return_value=(None, None))
    def test_main_no_config(self, mock_get_config):
        with self.assertRaises(SystemExit) as cm:
            main([])
        self.assertEqual(cm.exception.code, 1)

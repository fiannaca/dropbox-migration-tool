import unittest
from unittest.mock import patch, MagicMock
from src.main import main, get_config
import logging
import os

class TestConfig(unittest.TestCase):
    @patch('os.environ.get')
    @patch('configparser.ConfigParser.read')
    @patch('configparser.ConfigParser.get')
    def test_get_config_from_file(self, mock_config_get, mock_config_read, mock_env_get):
        mock_env_get.return_value = None
        mock_config_get.side_effect = ['test_key_file', 'test_secret_file']
        
        key, secret = get_config()
        mock_config_get.assert_called_with('dropbox', 'app_secret', fallback=None)
        self.assertEqual(key, 'test_key_file')
        self.assertEqual(secret, 'test_secret_file')

    
    @patch('os.environ.get')
    @patch('configparser.ConfigParser.read')
    @patch('configparser.ConfigParser.get')
    def test_get_team_config_from_file(self, mock_config_get, mock_config_read, mock_env_get):
        mock_env_get.return_value = None
        mock_config_get.side_effect = ['test_key_file', 'test_secret_file']
        
        key, secret = get_config(True)
        mock_config_get.assert_called_with('dropboxteam', 'app_secret', fallback=None)
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

    def tearDown(self):
        if os.path.exists('migration.log'):
            os.remove('migration.log')

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
    def test_main_new_dropbox_token_with_dry_run(self, MockMigration, mock_get_google_credentials, mock_save_dropbox_credentials, mock_get_dropbox_token, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        mock_load_dropbox_credentials.return_value = None
        mock_get_dropbox_token.return_value = 'new_token'
        main(['--dry_run'])
        mock_setup_logger.assert_called_once()
        mock_save_dropbox_credentials.assert_called_once_with('new_token', False)
        MockMigration.assert_called_once()

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('src.main.Migration')
    def test_main_with_src_and_dest_flags(self, MockMigration, mock_get_google_credentials, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        mock_load_dropbox_credentials.return_value = 'test_token'
        main(['--src', '/my_dropbox_path', '--dest', 'my_gdrive_path'])
        MockMigration.assert_called_once_with('test_token', mock_get_google_credentials.return_value, src_path='/my_dropbox_path', dest_path='my_gdrive_path', team_folder_id=None)

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('src.main.Migration')
    def test_main_with_team_flag(self, MockMigration, mock_get_google_credentials, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        mock_load_dropbox_credentials.return_value = 'test_token'
        main(['--team', '12345'])
        MockMigration.assert_called_once_with('test_token', mock_get_google_credentials.return_value, src_path=None, dest_path=None, team_folder_id='12345')

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('src.main.Migration')
    def test_main_list_teams_flag(self, MockMigration, mock_get_google_credentials, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        mock_load_dropbox_credentials.return_value = 'test_token'
        main(['--list-teams'])
        mock_setup_logger.assert_called_once()
        MockMigration.assert_called_once()
        migration_instance = MockMigration.return_value
        migration_instance.list_team_folders.assert_called_once()

    @patch('src.main.get_config', return_value=(None, None))
    def test_main_no_config(self, mock_get_config):
        with self.assertRaises(SystemExit) as cm:
            main([])
        self.assertEqual(cm.exception.code, 1)

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('src.main.get_dropbox_token')
    @patch('src.main.save_dropbox_credentials')
    @patch('os.remove')
    @patch('os.path.exists')
    @patch('src.main.Migration')
    def test_main_reauthentication_on_auth_error(self, MockMigration, mock_os_path_exists, mock_os_remove, mock_save_credentials, mock_get_dropbox_token, mock_get_google_credentials, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        import dropbox

        # First call to Migration raises AuthError, second call succeeds
        auth_error = dropbox.exceptions.AuthError('request_id', 'expired_access_token')
        auth_error.__str__ = lambda self: 'expired_access_token'
        MockMigration.side_effect = [
            auth_error,
            MagicMock()
        ]
        mock_load_dropbox_credentials.return_value = 'expired_token'
        mock_get_dropbox_token.return_value = 'new_token'
        mock_os_path_exists.return_value = True

        main([])

        # Verify that the credentials file was removed
        mock_os_remove.assert_called_once_with('dropbox_credentials.json')
        # Verify that a new token was requested and saved
        mock_get_dropbox_token.assert_called_once()
        mock_save_credentials.assert_called_once_with('new_token')
        # Verify that Migration was called twice
        self.assertEqual(MockMigration.call_count, 2)

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('src.main.Migration')
    def test_main_keyboard_interrupt(self, MockMigration, mock_get_google_credentials, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        # Simulate a KeyboardInterrupt during migration
        mock_migration_instance = MockMigration.return_value
        mock_migration_instance.start.side_effect = KeyboardInterrupt

        main([])

        # Verify that the summary is logged
        mock_migration_instance.log_migration_summary.assert_called_once()

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('os.remove')
    @patch('os.path.exists')
    @patch('src.main.Migration')
    def test_main_reauthentication_on_google_refresh_error(self, MockMigration, mock_os_path_exists, mock_os_remove, mock_get_google_credentials, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        from google.auth.exceptions import RefreshError

        # First call to Migration raises RefreshError, second call succeeds
        MockMigration.side_effect = [
            RefreshError(),
            MagicMock()
        ]
        mock_load_dropbox_credentials.return_value = 'test_token'
        # First call to get_google_credentials returns existing (but expired) creds
        # Second call will re-authenticate and return new creds
        mock_get_google_credentials.side_effect = [
            'expired_creds',
            'new_creds'
        ]
        mock_os_path_exists.return_value = True

        main([])

        # Verify that the credentials file was removed
        mock_os_remove.assert_called_once_with('google_token.json')
        # Verify that get_google_credentials was called twice
        self.assertEqual(mock_get_google_credentials.call_count, 2)
        # Verify that Migration was called twice
        self.assertEqual(MockMigration.call_count, 2)

    @patch('src.main.get_config', return_value=('test_key', 'test_secret'))
    @patch('src.main.setup_logger')
    @patch('src.main.load_dropbox_credentials')
    @patch('src.main.get_google_credentials')
    @patch('src.main.Migration')
    def test_main_ls_flag(self, MockMigration, mock_get_google_credentials, mock_load_dropbox_credentials, mock_setup_logger, mock_get_config):
        mock_load_dropbox_credentials.return_value = 'test_token'
        main(['--ls'])
        mock_setup_logger.assert_called_once()
        MockMigration.assert_called_once()
        migration_instance = MockMigration.return_value
        migration_instance.list_source_directory.assert_called_once()

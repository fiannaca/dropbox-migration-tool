import unittest
from unittest.mock import MagicMock, patch
from src.migration import Migration
import dropbox
import logging
import os

class TestMigration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def tearDown(self):
        if os.path.exists('migration_state.json'):
            os.remove('migration_state.json')

    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_process(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state):
        # Mock state management
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}

        # Mock Dropbox client and its return values
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Photos'),
            dropbox.files.FileMetadata(name='document.txt', path_display='/document.txt'),
            dropbox.files.FileMetadata(name='image.jpg', path_display='/Photos/image.jpg'),
        ]
        mock_dbx_client.download_file.return_value = True

        # Mock Google Drive client and its return values
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id_123'
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        # Instantiate and run the migration
        migration = Migration('fake_dbx_token', 'fake_gdrive_creds')
        migration.start()

        # Assertions
        # Check that folders were created
        mock_gdrive_client.create_folder.assert_called_once_with('Photos', parent_id=None)
        
        # Check that files were downloaded and uploaded
        self.assertEqual(mock_dbx_client.download_file.call_count, 2)
        self.assertEqual(mock_gdrive_client.upload_file.call_count, 2)
        
        mock_gdrive_client.upload_file.assert_any_call('/tmp/document.txt', 'document.txt', folder_id=None)
        mock_gdrive_client.upload_file.assert_any_call('/tmp/image.jpg', 'image.jpg', folder_id='folder_id_123')

    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_folder_conflict(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state):
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Photos'),
        ]
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = [{'id': 'existing_folder_id'}]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds')
        migration.start()

        mock_gdrive_client.create_folder.assert_not_called()
        self.assertEqual(migration.state['migrated_folders']['/Photos'], 'existing_folder_id')

    @patch('builtins.input', return_value='s')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_file_conflict_skip(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_input):
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name='document.txt', path_display='/document.txt'),
        ]
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = [{'id': 'existing_file_id'}]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds')
        migration.start()

        mock_dbx_client.download_file.assert_not_called()
        mock_gdrive_client.upload_file.assert_not_called()

    @patch('builtins.input', return_value='r')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_file_conflict_rename(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_input):
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name='document.txt', path_display='/document.txt'),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = [{'id': 'existing_file_id'}]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds')
        migration.start()

        mock_gdrive_client.upload_file.assert_called_once_with(unittest.mock.ANY, 'document (1).txt', folder_id=None)

    @patch('builtins.input', return_value='')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_test_run(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_input):
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name=f'file_{i}.txt', path_display=f'/file_{i}.txt') for i in range(15)
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.upload_file.return_value = 'file_id'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds')
        migration.start(test_run=True)

        self.assertEqual(mock_dbx_client.download_file.call_count, 10)
        self.assertEqual(mock_gdrive_client.upload_file.call_count, 10)
        self.assertEqual(mock_input.call_count, 10)

    @patch('builtins.input', side_effect=['', 's', 'esc'])
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_interactive_mode(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_input):
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Folder 1', path_display='/Folder 1'),
            dropbox.files.FileMetadata(name='file1.txt', path_display='/Folder 1/file1.txt'),
            dropbox.files.FolderMetadata(name='Folder 2', path_display='/Folder 2'),
            dropbox.files.FolderMetadata(name='Folder 3', path_display='/Folder 3'),
        ]
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds')
        migration.start(interactive=True)

        # Check that the first folder was migrated, the second was skipped, and the third was not reached
        self.assertIn('/Folder 1', migration.state['migrated_folders'])
        self.assertIn('/Folder 2', migration.state['skipped_folders'])
        self.assertNotIn('/Folder 3', migration.state['migrated_folders'])
        self.assertNotIn('/Folder 3', migration.state['skipped_folders'])
        
        # Check that save_state was called when skipping and quitting
        self.assertEqual(mock_save_state.call_count, 3) # 1 for migrated, 1 for skipped, 1 for quit

class TestMigrationWithSrcDestFlags(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def tearDown(self):
        if os.path.exists('migration_state.json'):
            os.remove('migration_state.json')

    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_src_flag(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state):
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Apps/MyApp/Photos'),
            dropbox.files.FileMetadata(name='image.jpg', path_display='/Apps/MyApp/Photos/image.jpg'),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id_123'
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', src_path='/Apps/MyApp')
        migration.start()

        mock_dbx_client.list_files_and_folders.assert_called_once_with(path='/Apps/MyApp')
        mock_gdrive_client.create_folder.assert_called_once_with('Photos', parent_id=None)
        mock_gdrive_client.upload_file.assert_called_once_with('/tmp/image.jpg', 'image.jpg', folder_id='folder_id_123')

    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_dest_flag(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state):
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {}, 'skipped_folders': []}
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Photos'),
            dropbox.files.FileMetadata(name='image.jpg', path_display='/Photos/image.jpg'),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_or_create_folder_path.return_value = 'dest_folder_id'
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id_123'
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', dest_path='MyCoolFolder/Backup')
        migration.start()

        mock_gdrive_client.find_or_create_folder_path.assert_called_once_with('MyCoolFolder/Backup')
        mock_gdrive_client.create_folder.assert_called_once_with('Photos', parent_id='dest_folder_id')
        mock_gdrive_client.upload_file.assert_called_once_with('/tmp/image.jpg', 'image.jpg', folder_id='folder_id_123')

    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_src_and_dest_flags(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state):
        mock_load_state.return_value = {'migrated_files': [], 'migrated_folders': {}, 'skipped_folders': []}
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Apps/MyApp/Photos'),
            dropbox.files.FileMetadata(name='image.jpg', path_display='/Apps/MyApp/Photos/image.jpg'),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_or_create_folder_path.return_value = 'dest_folder_id'
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id_123'
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', src_path='/Apps/MyApp', dest_path='MyCoolFolder/Backup')
        migration.start()

        mock_dbx_client.list_files_and_folders.assert_called_once_with(path='/Apps/MyApp')
        mock_gdrive_client.find_or_create_folder_path.assert_called_once_with('MyCoolFolder/Backup')
        mock_gdrive_client.create_folder.assert_called_once_with('Photos', parent_id='dest_folder_id')
        mock_gdrive_client.upload_file.assert_called_once_with('/tmp/image.jpg', 'image.jpg', folder_id='folder_id_123')

if __name__ == '__main__':
    unittest.main()

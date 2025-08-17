import unittest
from unittest.mock import MagicMock, patch
from src.migration import Migration
import dropbox
import logging
import os

TEST_STATE_FILE = 'test_migration_state.json'

class TestMigration(unittest.TestCase):

    def setUp(self):
        # A fresh state for each test
        self.mock_state = {
            'migrated_files': [], 
            'skipped_files': [], 
            'migrated_folders': {'/': None}, 
            'skipped_folders': []
        }

    def tearDown(self):
        if os.path.exists(TEST_STATE_FILE):
            os.remove(TEST_STATE_FILE)

    @patch('builtins.input', return_value='y')
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_process(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Photos'),
            dropbox.files.FileMetadata(name='document.txt', path_display='/document.txt', size=100),
            dropbox.files.FileMetadata(name='image.jpg', path_display='/Photos/image.jpg', size=200),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id_123'
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start()

        mock_gdrive_client.create_folder.assert_called_once_with('Photos', parent_id=None)
        self.assertEqual(mock_dbx_client.download_file.call_count, 2)
        self.assertEqual(mock_gdrive_client.upload_file.call_count, 2)
        mock_gdrive_client.upload_file.assert_any_call('/tmp/document.txt', 'document.txt', folder_id=None)
        mock_gdrive_client.upload_file.assert_any_call('/tmp/image.jpg', 'image.jpg', folder_id='folder_id_123')
        mock_tqdm.assert_called_with(total=300, unit='B', unit_scale=True, desc="Migrating files")
        pbar = mock_tqdm.return_value.__enter__.return_value
        pbar.update.assert_any_call(100)
        pbar.update.assert_any_call(200)

    @patch('builtins.input', return_value='y')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_folder_conflict(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Photos'),
        ]
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = [{'id': 'existing_folder_id'}]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start()

        mock_gdrive_client.create_folder.assert_not_called()
        self.assertEqual(migration.state['migrated_folders']['/Photos'], 'existing_folder_id')

    @patch('builtins.input', side_effect=['y', 's', 'y'])
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_file_conflict_skip_and_remember(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name='document.txt', path_display='/document.txt', size=100),
            dropbox.files.FileMetadata(name='document2.txt', path_display='/document2.txt', size=100),
        ]
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = [{'id': 'existing_file_id'}]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start()

        mock_dbx_client.download_file.assert_not_called()
        mock_gdrive_client.upload_file.assert_not_called()
        self.assertEqual(mock_input.call_count, 3)
        self.assertIn('/document.txt', migration.state['skipped_files'])
        self.assertIn('/document2.txt', migration.state['skipped_files'])

    @patch('builtins.input', side_effect=['y', 'r', 'y'])
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_file_conflict_rename(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name='document.txt', path_display='/document.txt', size=100),
            dropbox.files.FileMetadata(name='document2.txt', path_display='/document2.txt', size=100),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.side_effect = [[{'id': 'existing_file_id'}], [], [{'id': 'existing_file_id'}], []]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start()

        self.assertEqual(mock_gdrive_client.upload_file.call_count, 2)
        mock_gdrive_client.upload_file.assert_any_call(unittest.mock.ANY, 'document (1).txt', folder_id=None)
        mock_gdrive_client.upload_file.assert_any_call(unittest.mock.ANY, 'document2 (1).txt', folder_id=None)
        self.assertEqual(mock_input.call_count, 3)

    @patch('builtins.input', return_value='y')
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_failed_file_is_reported(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name='good_file.txt', path_display='/good_file.txt', size=100),
            dropbox.files.FileMetadata(name='bad_file.txt', path_display='/bad_file.txt', size=100),
        ]
        mock_dbx_client.download_file.side_effect = [True, Exception("Download failed")]
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.upload_file.return_value = 'file_id'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start()

        self.assertEqual(migration.migrated_in_session, 1)
        self.assertIn('/bad_file.txt', migration.failed_files)

    @patch('builtins.input', return_value='y')
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_special_characters(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        original_name = "Computer Systems - A Programmer's Persp. 2nd ed. - R. Bryant, D. O'Hallaron (Pearson, 2010) BBS.pdf"
        sanitized_name = "Computer Systems - A Programmer_s Persp. 2nd ed. - R. Bryant, D. O_Hallaron (Pearson, 2010) BBS.pdf"
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name=original_name, path_display=f'/{original_name}', size=100),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.upload_file.return_value = 'file_id'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start()

        mock_dbx_client.download_file.assert_called_once_with(f'/{original_name}', f'/tmp/{sanitized_name}', team_folder_id=None)
        mock_gdrive_client.upload_file.assert_called_once_with(f'/tmp/{sanitized_name}', original_name, folder_id=None)

    @patch('builtins.print')
    @patch('src.migration.Migration._load_state')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_dry_run(self, MockDropboxClient, MockGoogleDriveClient, mock_load_state, mock_print):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name='file1.txt', path_display='/file1.txt', size=100),
            dropbox.files.FileMetadata(name='file2.txt', path_display='/file2.txt', size=200),
        ]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start(dry_run=True)

        mock_print.assert_any_call(
            "--- Migration Plan Summary ---\n"
            "Files to migrate: 2\n"
            "--------------------------"
        )
        mock_print.assert_any_call("dropbox:/file1.txt -> gdrive:file1.txt")
        mock_print.assert_any_call("dropbox:/file2.txt -> gdrive:file2.txt")
        MockGoogleDriveClient.return_value.create_folder.assert_not_called()
        MockGoogleDriveClient.return_value.upload_file.assert_not_called()
        mock_dbx_client.download_file.assert_not_called()

    @patch('builtins.print')
    @patch('src.migration.Migration._load_state')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_dry_run_with_limit(self, MockDropboxClient, MockGoogleDriveClient, mock_load_state, mock_print):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name=f'file_{i}.txt', path_display=f'/file_{i}.txt', size=100) for i in range(5)
        ]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start(dry_run=True, limit=2)

        self.assertEqual(mock_print.call_count, 4) # 1 summary + 1 separator + 2 files
        mock_print.assert_any_call("dropbox:/file_0.txt -> gdrive:file_0.txt")
        mock_print.assert_any_call("dropbox:/file_1.txt -> gdrive:file_1.txt")

    @patch('builtins.print')
    @patch('src.migration.Migration._load_state')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_dry_run_with_src_and_dest(self, MockDropboxClient, MockGoogleDriveClient, mock_load_state, mock_print):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name='file1.txt', path_display='/src_folder/file1.txt', size=100),
        ]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', src_path='/src_folder', dest_path='dest_folder', state_file=TEST_STATE_FILE)
        migration.start(dry_run=True)

        mock_print.assert_any_call(
            "--- Migration Plan Summary ---\n"
            "Files to migrate: 1\n"
            "Source path: /src_folder\n"
            "Destination path: dest_folder\n"
            "--------------------------"
        )
        mock_print.assert_any_call("dropbox:/src_folder/file1.txt -> gdrive:dest_folder/file1.txt")

    @patch('builtins.input', return_value='y')
    @patch('builtins.print')
    @patch('src.migration.Migration._load_state')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_dry_run_large_migration_confirm(self, MockDropboxClient, MockGoogleDriveClient, mock_load_state, mock_print, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name=f'file_{i}.txt', path_display=f'/file_{i}.txt', size=100) for i in range(101)
        ]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start(dry_run=True)

        mock_print.assert_any_call("Warning: This will print a plan for 101 files.")
        self.assertEqual(mock_print.call_count, 104) # 1 summary + 1 separator + 1 warning + 101 files

    @patch('builtins.input', return_value='y')
    @patch('builtins.print')
    @patch('src.migration.Migration._load_state')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_dry_run_large_migration_with_limit(self, MockDropboxClient, MockGoogleDriveClient, mock_load_state, mock_print, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name=f'file_{i}.txt', path_display=f'/file_{i}.txt', size=100) for i in range(101)
        ]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start(dry_run=True, limit=20)

        # Assert that the warning is NOT printed
        for call in mock_print.call_args_list:
            self.assertNotIn("Warning", call.args[0])
        
        self.assertEqual(mock_print.call_count, 22) # 1 summary + 1 separator + 20 files
        mock_input.assert_not_called()

    @patch('builtins.input', return_value='n')
    @patch('builtins.print')
    @patch('src.migration.Migration._load_state')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_dry_run_large_migration_cancel(self, MockDropboxClient, MockGoogleDriveClient, mock_load_state, mock_print, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name=f'file_{i}.txt', path_display=f'/file_{i}.txt', size=100) for i in range(101)
        ]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start(dry_run=True)

        mock_print.assert_any_call("Warning: This will print a plan for 101 files.")
        mock_print.assert_any_call("Operation cancelled.")
        self.assertEqual(mock_print.call_count, 4) # 1 summary + 1 separator + 1 warning + 1 cancellation message

    @patch('builtins.input', side_effect=['', 's', 'esc'])
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_interactive_mode(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Folder 1', path_display='/Folder 1'),
            dropbox.files.FileMetadata(name='file1.txt', path_display='/Folder 1/file1.txt', size=100),
            dropbox.files.FolderMetadata(name='Folder 2', path_display='/Folder 2'),
            dropbox.files.FolderMetadata(name='Folder 3', path_display='/Folder 3'),
        ]
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start(interactive=True)

        self.assertIn('/Folder 1', migration.state['migrated_folders'])
        self.assertIn('/Folder 2', migration.state['skipped_folders'])
        self.assertNotIn('/Folder 3', migration.state['migrated_folders'])
        self.assertNotIn('/Folder 3', migration.state['skipped_folders'])
        self.assertEqual(mock_save_state.call_count, 3)

    @patch('builtins.input', return_value='y')
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_limit(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name=f'file_{i}.txt', path_display=f'/file_{i}.txt', size=100) for i in range(20)
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.upload_file.return_value = 'file_id'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.start(limit=15)

        self.assertEqual(mock_dbx_client.download_file.call_count, 15)
        self.assertEqual(mock_gdrive_client.upload_file.call_count, 15)

class TestMigrationWithSrcDestFlags(unittest.TestCase):

    def setUp(self):
        self.mock_state = {
            'migrated_files': [], 
            'skipped_files': [], 
            'migrated_folders': {'/': None}, 
            'skipped_folders': []
        }

    def tearDown(self):
        if os.path.exists(TEST_STATE_FILE):
            os.remove(TEST_STATE_FILE)

    @patch('builtins.input', return_value='y')
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_src_flag(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Apps/MyApp/Photos'),
            dropbox.files.FileMetadata(name='image.jpg', path_display='/Apps/MyApp/Photos/image.jpg', size=100),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id_123'
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', src_path='/Apps/MyApp', state_file=TEST_STATE_FILE)
        migration.start()

        mock_dbx_client.list_files_and_folders.assert_called_once_with(path='/Apps/MyApp', team_folder_id=None)
        mock_gdrive_client.create_folder.assert_called_once_with('Photos', parent_id=None)
        mock_gdrive_client.upload_file.assert_called_once_with('/tmp/image.jpg', 'image.jpg', folder_id='folder_id_123')

    @patch('builtins.input', return_value='y')
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_dest_flag(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Photos'),
            dropbox.files.FileMetadata(name='image.jpg', path_display='/Photos/image.jpg', size=100),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_or_create_folder_path.return_value = 'dest_folder_id'
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id_123'
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', dest_path='MyCoolFolder/Backup', state_file=TEST_STATE_FILE)
        migration.start()

        mock_gdrive_client.find_or_create_folder_path.assert_called_once_with('MyCoolFolder/Backup')
        mock_gdrive_client.create_folder.assert_called_once_with('Photos', parent_id='dest_folder_id')
        mock_gdrive_client.upload_file.assert_called_once_with('/tmp/image.jpg', 'image.jpg', folder_id='folder_id_123')

    @patch('builtins.input', return_value='y')
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_src_and_dest_flags(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FolderMetadata(name='Photos', path_display='/Apps/MyApp/Photos'),
            dropbox.files.FileMetadata(name='image.jpg', path_display='/Apps/MyApp/Photos/image.jpg', size=100),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_or_create_folder_path.return_value = 'dest_folder_id'
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.create_folder.return_value = 'folder_id_123'
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', src_path='/Apps/MyApp', dest_path='MyCoolFolder/Backup', state_file=TEST_STATE_FILE)
        migration.start()

        mock_dbx_client.list_files_and_folders.assert_called_once_with(path='/Apps/MyApp', team_folder_id=None)
        mock_gdrive_client.find_or_create_folder_path.assert_called_once_with('MyCoolFolder/Backup')
        mock_gdrive_client.create_folder.assert_called_once_with('Photos', parent_id='dest_folder_id')
        mock_gdrive_client.upload_file.assert_called_once_with('/tmp/image.jpg', 'image.jpg', folder_id='folder_id_123')

class TestMigrationWithTeamFlag(unittest.TestCase):

    def setUp(self):
        self.mock_state = {
            'migrated_files': [], 
            'skipped_files': [], 
            'migrated_folders': {'/': None}, 
            'skipped_folders': []
        }

    def tearDown(self):
        if os.path.exists(TEST_STATE_FILE):
            os.remove(TEST_STATE_FILE)

    @patch('builtins.input', return_value='y')
    @patch('src.migration.tqdm')
    @patch('src.migration.Migration._save_state')
    @patch('src.migration.Migration._load_state')
    @patch('os.remove')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_migration_with_team_flag(self, MockDropboxClient, MockGoogleDriveClient, mock_os_remove, mock_load_state, mock_save_state, mock_tqdm, mock_input):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_dbx_client.list_files_and_folders.return_value = [
            dropbox.files.FileMetadata(name='team_file.txt', path_display='/team_file.txt', size=100),
        ]
        mock_dbx_client.download_file.return_value = True
        mock_gdrive_client = MockGoogleDriveClient.return_value
        mock_gdrive_client.find_file.return_value = []
        mock_gdrive_client.upload_file.return_value = 'file_id_456'

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', team_folder_id='12345', state_file=TEST_STATE_FILE)
        migration.start()

        mock_dbx_client.list_files_and_folders.assert_called_once_with(path='', team_folder_id='12345')
        mock_dbx_client.download_file.assert_called_once_with('/team_file.txt', '/tmp/team_file.txt', team_folder_id='12345')
        mock_gdrive_client.upload_file.assert_called_once_with('/tmp/team_file.txt', 'team_file.txt', folder_id=None)

    @patch('builtins.print')
    @patch('src.migration.Migration._load_state')
    @patch('src.migration.GoogleDriveClient')
    @patch('src.migration.DropboxClient')
    def test_list_team_folders(self, MockDropboxClient, MockGoogleDriveClient, mock_load_state, mock_print):
        mock_load_state.return_value = self.mock_state
        mock_dbx_client = MockDropboxClient.return_value
        mock_folder1 = MagicMock()
        mock_folder1.name = 'Folder 1'
        mock_folder1.team_folder_id = '123'
        mock_folder2 = MagicMock()
        mock_folder2.name = 'Folder 2'
        mock_folder2.team_folder_id = '456'
        mock_dbx_client.list_team_folders.return_value = [mock_folder1, mock_folder2]

        migration = Migration('fake_dbx_token', 'fake_gdrive_creds', state_file=TEST_STATE_FILE)
        migration.list_team_folders()

        mock_print.assert_any_call("Available team folders:")
        mock_print.assert_any_call("- Folder 1 (ID: 123)")
        mock_print.assert_any_call("- Folder 2 (ID: 456)")


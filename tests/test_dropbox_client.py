import unittest
from unittest.mock import patch, MagicMock
from src.dropbox_client import DropboxClient
import dropbox
import logging

class TestDropboxClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def setUp(self):
        self.mock_dbx = MagicMock()
        self.client = DropboxClient('test_token')
        self.client.dbx = self.mock_dbx

    def test_list_files_and_folders_success(self):
        mock_result = MagicMock()
        mock_result.entries = ['file1', 'folder1']
        mock_result.has_more = False  # Explicitly set has_more to False
        self.mock_dbx.files_list_folder.return_value = mock_result
        
        items = self.client.list_files_and_folders('/test_path', recursive=True)
        self.mock_dbx.files_list_folder.assert_called_with('/test_path', recursive=True)
        self.assertEqual(items, ['file1', 'folder1'])

    def test_list_files_and_folders_with_pagination(self):
        # Mock the first page of results
        mock_result1 = MagicMock()
        mock_result1.entries = ['file1', 'folder1']
        mock_result1.has_more = True
        mock_result1.cursor = 'cursor123'
        
        # Mock the second page of results
        mock_result2 = MagicMock()
        mock_result2.entries = ['file2', 'folder2']
        mock_result2.has_more = False

        self.mock_dbx.files_list_folder.return_value = mock_result1
        self.mock_dbx.files_list_folder_continue.return_value = mock_result2

        items = self.client.list_files_and_folders('/test_path', recursive=True)

        self.mock_dbx.files_list_folder.assert_called_once_with('/test_path', recursive=True)
        self.mock_dbx.files_list_folder_continue.assert_called_once_with('cursor123')
        self.assertEqual(items, ['file1', 'folder1', 'file2', 'folder2'])

    def test_list_files_and_folders_failure(self):
        self.mock_dbx.files_list_folder.side_effect = dropbox.exceptions.ApiError('request_id', 'error', 'user_message_text', 'user_message_locale')
        with self.assertRaises(dropbox.exceptions.ApiError):
            self.client.list_files_and_folders('/test_path')

    def test_download_file_success(self):
        result = self.client.download_file('/dbx_path', '/local_path')
        self.mock_dbx.files_download_to_file.assert_called_with('/local_path', '/dbx_path')
        self.assertTrue(result)

    def test_download_file_failure(self):
        self.mock_dbx.files_download_to_file.side_effect = dropbox.exceptions.ApiError('request_id', 'error', 'user_message_text', 'user_message_locale')
        with self.assertRaises(dropbox.exceptions.ApiError):
            self.client.download_file('/dbx_path', '/local_path')

if __name__ == '__main__':
    unittest.main()

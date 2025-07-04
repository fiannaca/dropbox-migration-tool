import unittest
from unittest.mock import patch, MagicMock
from src.google_drive_client import GoogleDriveClient
import logging

class TestGoogleDriveClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    @patch('src.google_drive_client.build')
    def setUp(self, mock_build):
        self.mock_service = MagicMock()
        mock_build.return_value = self.mock_service
        self.client = GoogleDriveClient(MagicMock())
        self.client.service = self.mock_service

    def test_create_folder_success(self):
        mock_folder = {'id': 'folder_id_123'}
        self.mock_service.files().create().execute.return_value = mock_folder
        
        folder_id = self.client.create_folder('MyFolder', parent_id='parent_id_456')
        self.assertEqual(folder_id, 'folder_id_123')

    def test_create_folder_failure(self):
        self.mock_service.files().create().execute.side_effect = Exception('Test Error')
        with self.assertRaises(Exception):
            self.client.create_folder('MyFolder')

    @patch('src.google_drive_client.MediaFileUpload')
    def test_upload_file_success(self, MockMediaFileUpload):
        mock_file = {'id': 'file_id_789'}
        self.mock_service.files().create().execute.return_value = mock_file
        
        file_id = self.client.upload_file('/local_path', 'my_file.txt', folder_id='folder_id_123')
        self.assertEqual(file_id, 'file_id_789')

    def test_find_file_success(self):
        mock_response = {'files': [{'id': 'file_id_123', 'name': 'MyFile.txt'}]}
        self.mock_service.files().list().execute.return_value = mock_response
        
        files = self.client.find_file('MyFile.txt', parent_id='parent_id_456')
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['id'], 'file_id_123')

    def test_find_file_with_single_quote(self):
        self.client.find_file("Programmer's Persp.pdf")
        self.mock_service.files().list.assert_called_with(
            q='name = "Programmer\'s Persp.pdf" and \'root\' in parents',
            spaces='drive',
            fields='files(id, name)'
        )

    def test_find_file_with_double_quote(self):
        self.client.find_file('My "Cool" File.txt')
        self.mock_service.files().list.assert_called_with(
            q='name = "My \"Cool\" File.txt" and \'root\' in parents',
            spaces='drive',
            fields='files(id, name)'
        )

    def test_find_file_failure(self):
        self.mock_service.files().list().execute.side_effect = Exception('Test Error')
        with self.assertRaises(Exception):
            self.client.find_file('MyFile.txt')

    @patch('src.google_drive_client.MediaFileUpload')
    def test_upload_file_failure(self, MockMediaFileUpload):
        self.mock_service.files().create().execute.side_effect = Exception('Test Error')
        with self.assertRaises(Exception):
            self.client.upload_file('/local_path', 'my_file.txt')

if __name__ == '__main__':
    unittest.main()
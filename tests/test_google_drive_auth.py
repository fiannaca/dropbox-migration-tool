import unittest
from unittest.mock import patch, mock_open
from src.google_drive_auth import get_credentials

class TestGoogleDriveAuth(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    @patch('google.oauth2.credentials.Credentials.from_authorized_user_file')
    def test_get_credentials_from_token(self, mock_from_file, mock_exists):
        mock_creds = mock_from_file.return_value
        mock_creds.valid = True
        creds = get_credentials()
        self.assertEqual(creds, mock_creds)
        mock_from_file.assert_called_with('google_token.json', ['https://www.googleapis.com/auth/drive'])

    @patch('os.path.exists', side_effect=[False, True]) # token.json doesn't exist, client_secrets.json does
    @patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file')
    def test_get_credentials_new_flow(self, mock_from_secrets, mock_exists):
        mock_flow = mock_from_secrets.return_value
        mock_creds = mock_flow.run_local_server.return_value
        
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            creds = get_credentials()
            self.assertEqual(creds, mock_creds)
            mock_from_secrets.assert_called_with('client_secrets.json', ['https://www.googleapis.com/auth/drive'])
            mock_file.assert_called_with('google_token.json', 'w')
            mock_file().write.assert_called_with(mock_creds.to_json())

if __name__ == '__main__':
    unittest.main()
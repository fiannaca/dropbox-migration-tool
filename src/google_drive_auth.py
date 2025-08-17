import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import logging

TOKEN_PATH = 'google_token.json'
CLIENT_SECRETS_PATH = 'google_credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_credentials():
    """
    Gets Google Drive credentials.
    It handles the OAuth 2.0 flow and token refresh.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logging.error(f"Failed to refresh Google token: {e}")
                creds = None # Force re-authentication
        
        if not creds:
            if not os.path.exists(CLIENT_SECRETS_PATH):
                logging.error(f"'{CLIENT_SECRETS_PATH}' not found. Please download it from the Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            
    return creds
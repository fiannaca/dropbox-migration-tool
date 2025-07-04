import os
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import logging

CREDENTIALS_PATH = 'google_credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_credentials(credentials_path=CREDENTIALS_PATH):
    creds = None
    if os.path.exists(credentials_path):
        creds = Credentials.from_authorized_user_file(credentials_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(credentials_path, 'w') as token:
            token.write(creds.to_json())
            
    return creds

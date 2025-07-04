from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import logging
from src.retry import retry_on_exception

def is_retryable_error(e):
    if isinstance(e, HttpError):
        return e.resp.status in [429, 500, 502, 503, 504]
    return False

class GoogleDriveClient:
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    @retry_on_exception(HttpError, should_retry=is_retryable_error)
    def create_folder(self, name, parent_id=None):
        """
        Creates a folder in Google Drive.
        """
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        try:
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            logging.info(f"Created folder '{name}' with ID: {folder.get('id')}")
            return folder.get('id')
        except HttpError as e:
            logging.error(f"An error occurred while creating folder '{name}': {e}")
            raise e

    @retry_on_exception(HttpError, should_retry=is_retryable_error)
    def find_file(self, name, parent_id=None):
        """
        Finds a file or folder by name in a specific parent folder.
        """
        # Escape backslashes and double quotes in the file name
        name = name.replace('', '').replace('"', '"')
        query = f'name = "{name}"'
        if parent_id:
            query += f" and '{parent_id}' in parents"
        else:
            query += " and 'root' in parents"
        
        try:
            response = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            return response.get('files', [])
        except HttpError as e:
            logging.error(f"An error occurred while searching for file '{name}': {e}")
            raise e

    @retry_on_exception(HttpError, should_retry=is_retryable_error)
    def upload_file(self, local_path, file_name, folder_id=None):
        """
        Uploads a file to Google Drive.
        """
        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(local_path, resumable=True)
        
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            logging.info(f"Successfully uploaded {file_name} with ID: {file.get('id')}")
            return file.get('id')
        except HttpError as e:
            logging.error(f"An error occurred while uploading file '{file_name}': {e}")
            raise e

    def find_or_create_folder_path(self, path):
        """
        Finds or creates a nested folder structure and returns the ID of the last folder.
        """
        current_parent_id = None
        for folder_name in path.split('/'):
            if not folder_name:
                continue
            
            existing_folders = self.find_file(folder_name, parent_id=current_parent_id)
            if existing_folders:
                current_parent_id = existing_folders[0]['id']
            else:
                current_parent_id = self.create_folder(folder_name, parent_id=current_parent_id)
        
        return current_parent_id

import dropbox
import logging
from src.retry import retry_on_exception

class DropboxClient:
    def __init__(self, access_token):
        self.dbx = dropbox.Dropbox(access_token)

    @retry_on_exception((dropbox.exceptions.RateLimitError, dropbox.exceptions.ApiError))
    def list_files_and_folders(self, path=''):
        """
        Recursively lists all files and folders in a given Dropbox path.
        """
        try:
            result = self.dbx.files_list_folder(path, recursive=True)
            return result.entries
        except dropbox.exceptions.ApiError as err:
            logging.error(f"Failed to list folder: {err}")
            # Reraise the exception to be caught by the decorator
            raise err

    @retry_on_exception((dropbox.exceptions.RateLimitError, dropbox.exceptions.ApiError))
    def download_file(self, dropbox_path, local_path):
        """
        Downloads a file from Dropbox.
        """
        try:
            self.dbx.files_download_to_file(local_path, dropbox_path)
            logging.info(f"Successfully downloaded {dropbox_path} to {local_path}")
            return True
        except dropbox.exceptions.ApiError as err:
            logging.error(f"Failed to download file: {err}")
            # Reraise the exception to be caught by the decorator
            raise err

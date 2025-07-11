import dropbox
import logging
from src.retry import retry_on_exception

class DropboxClient:
    def __init__(self, access_token):
        self.dbx = dropbox.Dropbox(access_token)

    @retry_on_exception((dropbox.exceptions.RateLimitError, dropbox.exceptions.ApiError))
    def list_files_and_folders(self, path='', recursive=False):
        """
        Lists all files and folders in a given Dropbox path, handling pagination.
        """
        try:
            result = self.dbx.files_list_folder(path, recursive=recursive)
            all_entries = result.entries
            
            if recursive:
                while result.has_more:
                    result = self.dbx.files_list_folder_continue(result.cursor)
                    all_entries.extend(result.entries)
                
            return all_entries
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

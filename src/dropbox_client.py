import dropbox
import logging
from src.retry import retry_on_exception
from dropbox.common import PathRoot

class DropboxClient:
    def __init__(self, access_token):
        self.dbx = dropbox.Dropbox(access_token)
        self.dbx_team = dropbox.DropboxTeam(access_token)

    @retry_on_exception((dropbox.exceptions.RateLimitError, dropbox.exceptions.ApiError))
    def list_team_folders(self):
        """
        Lists all team folders.
        """
        try:
            result = self.dbx_team.team_folder_list()
            return result.team_folders
        except dropbox.exceptions.ApiError as err:
            logging.error(f"Failed to list team folders: {err}")
            raise err

    def _get_dbx_instance(self, team_folder_id=None):
        """
        Returns the correct Dropbox API instance based on whether a team folder is being accessed.
        """
        if team_folder_id:
            return self.dbx.with_path_root(PathRoot.namespace_id(team_folder_id))
        return self.dbx

    @retry_on_exception((dropbox.exceptions.RateLimitError, dropbox.exceptions.ApiError))
    def list_files_and_folders(self, path='', recursive=False, team_folder_id=None):
        """
        Lists all files and folders in a given Dropbox path, handling pagination.
        """
        dbx_instance = self._get_dbx_instance(team_folder_id)
        try:
            result = dbx_instance.files_list_folder(path, recursive=recursive)
            all_entries = result.entries
            
            if recursive:
                while result.has_more:
                    result = dbx_instance.files_list_folder_continue(result.cursor)
                    all_entries.extend(result.entries)
                
            return all_entries
        except dropbox.exceptions.ApiError as err:
            logging.error(f"Failed to list folder: {err}")
            # Reraise the exception to be caught by the decorator
            raise err

    @retry_on_exception((dropbox.exceptions.RateLimitError, dropbox.exceptions.ApiError))
    def download_file(self, dropbox_path, local_path, team_folder_id=None):
        """
        Downloads a file from Dropbox.
        """
        dbx_instance = self._get_dbx_instance(team_folder_id)
        try:
            dbx_instance.files_download_to_file(local_path, dropbox_path)
            logging.info(f"Successfully downloaded {dropbox_path} to {local_path}")
            return True
        except dropbox.exceptions.ApiError as err:
            logging.error(f"Failed to download file: {err}")
            # Reraise the exception to be caught by the decorator
            raise err

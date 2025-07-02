import os
import json
import dropbox
import logging
from src.dropbox_client import DropboxClient
from src.google_drive_client import GoogleDriveClient

class Migration:
    def __init__(self, dropbox_token, google_credentials, state_file='migration_state.json'):
        self.dropbox_client = DropboxClient(dropbox_token)
        self.google_drive_client = GoogleDriveClient(google_credentials)
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self):
        """Loads the migration state from a file."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {'migrated_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}

    def _save_state(self):
        """Saves the migration state to a file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def start(self, test_run=False, interactive=False):
        """Starts the migration process."""
        if test_run:
            logging.info("Starting test run...")
        elif interactive:
            logging.info("Starting interactive migration...")
        else:
            logging.info("Starting migration...")
        
        dropbox_items = self.dropbox_client.list_files_and_folders()

        if not dropbox_items:
            logging.info("No items to migrate.")
            return

        if self._migrate_folders(dropbox_items, interactive=interactive) is False:
            # User chose to quit
            return

        files_to_migrate = [item for item in dropbox_items if isinstance(item, dropbox.files.FileMetadata) and item.path_display not in self.state['migrated_files']]
        
        if test_run:
            self._migrate_files(files_to_migrate[:10], test_run=True)
        else:
            self._migrate_files(files_to_migrate)

        logging.info("Migration complete.")

    def _migrate_folders(self, items, interactive=False):
        """Migrates folders from Dropbox to Google Drive, preserving hierarchy."""
        folders = [item for item in items if isinstance(item, dropbox.files.FolderMetadata)]
        # Sort folders by path depth to ensure parents are created before children
        folders.sort(key=lambda f: f.path_display.count('/'))

        for folder in folders:
            if folder.path_display in self.state['migrated_folders'] or folder.path_display in self.state['skipped_folders']:
                continue

            if interactive:
                files_in_folder = [item.name for item in items if isinstance(item, dropbox.files.FileMetadata) and os.path.dirname(item.path_display) == folder.path_display]
                logging.info(f"\nFolder: {folder.path_display}")
                if files_in_folder:
                    logging.info("Files to be migrated in this folder:")
                    for file_name in files_in_folder:
                        logging.info(f"- {file_name}")
                else:
                    logging.info("This folder is empty.")
                
                choice = input("Press Enter to continue, 's' to skip this folder, or 'esc' to quit: ").lower()
                if choice == 's':
                    self.state['skipped_folders'].append(folder.path_display)
                    self._save_state()
                    continue
                elif choice == 'esc':
                    logging.info("Quitting migration.")
                    self._save_state()
                    return False

            parent_path = os.path.dirname(folder.path_display)
            if parent_path == '/':
                parent_path = '/' 
            
            parent_id = self.state['migrated_folders'].get(parent_path)

            existing_folders = self.google_drive_client.find_file(folder.name, parent_id=parent_id)
            if existing_folders:
                folder_id = existing_folders[0]['id']
                logging.info(f"Folder '{folder.name}' already exists. Using existing folder.")
            else:
                folder_id = self.google_drive_client.create_folder(folder.name, parent_id=parent_id)

            if folder_id:
                self.state['migrated_folders'][folder.path_display] = folder_id
                self._save_state()

    def _migrate_files(self, files, test_run=False):
        """Migrates files from Dropbox to Google Drive."""
        for file in files:
            if file.path_display not in self.state['migrated_files']:
                parent_path = os.path.dirname(file.path_display)
                if parent_path == '/':
                    parent_path = '/'

                parent_folder_id = self.state['migrated_folders'].get(parent_path)
                
                existing_files = self.google_drive_client.find_file(file.name, parent_id=parent_folder_id)
                
                if existing_files:
                    action = self._handle_file_conflict(file)
                    if action == 'skip':
                        continue
                    elif action == 'rename':
                        # This is a naive rename, a more robust implementation would check for conflicts on the new name
                        file.name = f"{os.path.splitext(file.name)[0]} (1){os.path.splitext(file.name)[1]}"
                
                local_path = f"/tmp/{file.name}" # Using /tmp for temporary downloads
                if self.dropbox_client.download_file(file.path_display, local_path):
                    file_id = self.google_drive_client.upload_file(local_path, file.name, folder_id=parent_folder_id)
                    if file_id:
                        self.state['migrated_files'].append(file.path_display)
                        self._save_state()
                    os.remove(local_path)
                
                if test_run:
                    input("Press Enter to continue to the next file...")

    def _handle_file_conflict(self, file):
        """Prompts the user to resolve a file conflict."""
        while True:
            choice = input(f"File '{file.name}' already exists. Overwrite, rename, or skip? (o/r/s): ").lower()
            if choice in ['o', 'r', 's']:
                if choice == 'o':
                    return 'overwrite'
                elif choice == 'r':
                    return 'rename'
                else:
                    return 'skip'
            logging.warning("Invalid choice. Please enter 'o', 'r', or 's'.")

import os
import json
import dropbox
import logging
from tqdm import tqdm
from src.dropbox_client import DropboxClient
from src.google_drive_client import GoogleDriveClient

class Migration:
    def __init__(self, dropbox_token, google_credentials, src_path=None, dest_path=None, state_file='migration_state.json'):
        self.dropbox_client = DropboxClient(dropbox_token)
        self.google_drive_client = GoogleDriveClient(google_credentials)
        self.src_path = src_path
        self.dest_path = dest_path
        self.state_file = state_file
        self.state = self._load_state()
        self.total_files_to_migrate = 0
        self.migrated_in_session = 0
        self.conflict_resolution_strategy = None

    def _load_state(self):
        """Loads the migration state from a file."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {'migrated_files': [], 'skipped_files': [], 'migrated_folders': {'/': None}, 'skipped_folders': []}

    def _save_state(self):
        """Saves the migration state to a file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def start(self, dry_run=False, interactive=False, limit=None):
        """Starts the migration process."""
        if dry_run:
            print("Generating migration plan (dry run)...")
            logging.info("Generating migration plan (dry run)...")
            self._generate_migration_plan(limit=limit)
            return

        if interactive:
            print("Starting interactive migration...")
            logging.info("Starting interactive migration...")
        else:
            print("Starting migration...")
            logging.info("Starting migration...")

        dest_folder_id = None
        if self.dest_path:
            dest_folder_id = self.google_drive_client.find_or_create_folder_path(self.dest_path)
            self.state['migrated_folders'][self.dest_path] = dest_folder_id

        dropbox_items = self.dropbox_client.list_files_and_folders(path=self.src_path or '')

        if not dropbox_items:
            print("No items to migrate.")
            logging.info("No items to migrate.")
            return

        if self._migrate_folders(dropbox_items, interactive=interactive, dest_folder_id=dest_folder_id) is False:
            # User chose to quit
            return

        files_to_migrate = [
            item for item in dropbox_items 
            if isinstance(item, dropbox.files.FileMetadata) 
            and item.path_display not in self.state['migrated_files']
            and item.path_display not in self.state['skipped_files']
        ]
        self.total_files_to_migrate = len(files_to_migrate)

        if not files_to_migrate:
            print("All files have already been migrated.")
            logging.info("All files have already been migrated.")
            return
            
        total_size = sum(f.size for f in files_to_migrate)
        
        summary = (
            f"--- Migration Summary ---\n"
            f"Total files to migrate: {self.total_files_to_migrate}\n"
            f"Total size: {total_size / 1e6:.2f} MB"
        )
        if self.src_path:
            summary += f"\nSource path: {self.src_path}"
        if self.dest_path:
            summary += f"\nDestination path: {self.dest_path}"
        print(summary)
        logging.info(summary)
        
        choice = input("Do you want to proceed with the migration? (y/n): ").lower()
        if choice != 'y':
            print("Migration cancelled.")
            logging.info("Migration cancelled by user.")
            return

        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Migrating files") as pbar:
            self.migrated_in_session = self._migrate_files(files_to_migrate, pbar, dest_folder_id=dest_folder_id, limit=limit)

        print("Migration complete.")
        logging.info("Migration complete.")
        self.log_migration_summary()

    def log_migration_summary(self):
        """Logs and prints a summary of the migration session."""
        remaining_files = self.total_files_to_migrate - self.migrated_in_session
        summary = (
            f"--- Migration Session Summary ---\n"
            f"Migrated this session: {self.migrated_in_session}\n"
            f"Remaining to migrate: {remaining_files}\n"
            f"Total migrated: {len(self.state['migrated_files'])}\n"
            f"---------------------------------"
        )
        logging.info(summary)
        print(summary)

    def _generate_migration_plan(self, limit=None):
        """Generates and prints a plan of files to be migrated."""
        dropbox_items = self.dropbox_client.list_files_and_folders(path=self.src_path or '')
        files_to_migrate = [item for item in dropbox_items if isinstance(item, dropbox.files.FileMetadata) and item.path_display not in self.state['migrated_files']]

        summary = (
            f"--- Migration Plan Summary ---\n"
            f"Files to migrate: {len(files_to_migrate)}"
        )
        if self.src_path:
            summary += f"\nSource path: {self.src_path}"
        if self.dest_path:
            summary += f"\nDestination path: {self.dest_path}"
        summary += "\n--------------------------"
        print(summary)
        logging.info(summary)

        if not files_to_migrate:
            return

        if limit is None and len(files_to_migrate) > 100:
            warning = f"Warning: This will print a plan for {len(files_to_migrate)} files."
            print(warning)
            logging.warning(warning)
            choice = input("Do you want to continue? (y/n): ").lower()
            if choice != 'y':
                print("Operation cancelled.")
                logging.info("Operation cancelled by user.")
                return
        
        for i, file in enumerate(files_to_migrate):
            if limit is not None and i >= limit:
                break
            
            dest_path = self._get_destination_path(file)
            plan_line = f"dropbox:{file.path_display} -> gdrive:{dest_path}"
            print(plan_line)
            logging.info(plan_line)

    def _get_destination_path(self, file):
        """Calculates the destination path in Google Drive for a given file."""
        if self.src_path:
            relative_path = os.path.relpath(file.path_display, self.src_path)
        else:
            relative_path = file.path_display.lstrip('/')

        if self.dest_path:
            return os.path.join(self.dest_path, relative_path)
        else:
            return relative_path

    def _migrate_folders(self, items, interactive=False, dest_folder_id=None):
        """Migrates folders from Dropbox to Google Drive, preserving hierarchy."""
        folders = [item for item in items if isinstance(item, dropbox.files.FolderMetadata)]
        folders.sort(key=lambda f: f.path_display.count('/'))

        for folder in folders:
            if folder.path_display in self.state['migrated_folders'] or folder.path_display in self.state['skipped_folders']:
                continue

            if interactive:
                folder_info = f"\nFolder: {folder.path_display}"
                print(folder_info)
                logging.info(folder_info)
                files_in_folder = [item.name for item in items if isinstance(item, dropbox.files.FileMetadata) and os.path.dirname(item.path_display) == folder.path_display]
                if files_in_folder:
                    print("Files to be migrated in this folder:")
                    logging.info("Files to be migrated in this folder:")
                    for file_name in files_in_folder:
                        print(f"- {file_name}")
                        logging.info(f"- {file_name}")
                else:
                    print("This folder is empty.")
                    logging.info("This folder is empty.")
                
                choice = input("Press Enter to continue, 's' to skip this folder, or 'esc' to quit: ").lower()
                if choice == 's':
                    self.state['skipped_folders'].append(folder.path_display)
                    self._save_state()
                    continue
                elif choice == 'esc':
                    print("Quitting migration.")
                    logging.info("Quitting migration.")
                    self._save_state()
                    return False

            parent_dropbox_path = os.path.dirname(folder.path_display)
            if self.src_path and parent_dropbox_path.startswith(self.src_path):
                relative_parent_path = os.path.relpath(parent_dropbox_path, self.src_path)
                if relative_parent_path == '.':
                    parent_path = self.dest_path or '/'
                else:
                    parent_path = os.path.join(self.dest_path or '/', relative_parent_path)
            else:
                parent_path = parent_dropbox_path

            parent_id = self.state['migrated_folders'].get(parent_path)

            if parent_id is None:
                if self.dest_path:
                    parent_id = self.state['migrated_folders'].get(self.dest_path)
                elif parent_path == '/':
                    parent_id = self.state['migrated_folders'].get('/')

            existing_folders = self.google_drive_client.find_file(folder.name, parent_id=parent_id)
            if existing_folders:
                folder_id = existing_folders[0]['id']
                logging.info(f"Folder '{folder.name}' already exists. Using existing folder.")
            else:
                folder_id = self.google_drive_client.create_folder(folder.name, parent_id=parent_id)

            if folder_id:
                if self.src_path:
                    relative_folder_path = os.path.relpath(folder.path_display, self.src_path)
                    migrated_path = os.path.join(self.dest_path or '/', relative_folder_path)
                else:
                    migrated_path = folder.path_display

                self.state['migrated_folders'][migrated_path] = folder_id
                self.state['migrated_folders'][folder.path_display] = folder_id
                self._save_state()

    def _migrate_files(self, files, pbar, dest_folder_id=None, limit=None):
        """Migrates files from Dropbox to Google Drive."""
        migrated_count = 0
        for file in files:
            if limit is not None and migrated_count >= limit:
                logging.info(f"Reached migration limit of {limit} files.")
                break

            if file.path_display not in self.state['migrated_files']:
                pbar.set_description(f"Downloading {file.name} ({file.size / 1e6:.2f} MB)")
                parent_dropbox_path = os.path.dirname(file.path_display)
                
                if self.src_path:
                    relative_parent_path = os.path.relpath(parent_dropbox_path, self.src_path)
                    if relative_parent_path == '.':
                        migrated_parent_path = self.dest_path or '/'
                    else:
                        migrated_parent_path = os.path.join(self.dest_path or '/', relative_parent_path)
                else:
                    migrated_parent_path = parent_dropbox_path

                parent_folder_id = self.state['migrated_folders'].get(migrated_parent_path)

                if parent_folder_id is None:
                    if self.dest_path:
                        parent_folder_id = self.state['migrated_folders'].get(self.dest_path)
                    elif migrated_parent_path == '/':
                        parent_folder_id = self.state['migrated_folders'].get('/')

                existing_files = self.google_drive_client.find_file(file.name, parent_id=parent_folder_id)
                
                if existing_files:
                    action = self.conflict_resolution_strategy or self._handle_file_conflict(file, parent_folder_id)
                    if action == 'skip':
                        if file.path_display not in self.state['skipped_files']:
                            self.state['skipped_files'].append(file.path_display)
                            self._save_state()
                        pbar.update(file.size)
                        continue
                    elif action == 'rename':
                        file.name = self._get_unique_name(file.name, parent_folder_id)
                
                local_path = f"/tmp/{file.name}"
                if self.dropbox_client.download_file(file.path_display, local_path):
                    pbar.set_description(f"Uploading {file.name} ({file.size / 1e6:.2f} MB)")
                    file_id = self.google_drive_client.upload_file(local_path, file.name, folder_id=parent_folder_id)
                    if file_id:
                        self.state['migrated_files'].append(file.path_display)
                        self._save_state()
                        migrated_count += 1
                        pbar.update(file.size)
                    os.remove(local_path)
        return migrated_count

    def _handle_file_conflict(self, file, parent_folder_id):
        """Prompts the user to resolve a file conflict."""
        if self.conflict_resolution_strategy:
            return self.conflict_resolution_strategy

        while True:
            choice = input(f"File '{file.name}' already exists. Overwrite, rename, or skip? (o/r/s): ").lower()
            if choice in ['o', 'r', 's']:
                action = {'o': 'overwrite', 'r': 'rename', 's': 'skip'}[choice]
                
                remember_choice = input(f"Always {action.upper()} for future conflicts? (y/n): ").lower()
                if remember_choice == 'y':
                    self.conflict_resolution_strategy = action
                
                if action == 'skip':
                    self.state['skipped_files'].append(file.path_display)
                    self._save_state()

                return action
            logging.warning("Invalid choice. Please enter 'o', 'r', or 's'.")

    def _get_unique_name(self, original_name, parent_folder_id):
        """Generates a unique file name if a conflict exists."""
        name, ext = os.path.splitext(original_name)
        counter = 1
        new_name = f"{name} ({counter}){ext}"
        while self.google_drive_client.find_file(new_name, parent_id=parent_folder_id):
            counter += 1
            new_name = f"{name} ({counter}){ext}"
        return new_name

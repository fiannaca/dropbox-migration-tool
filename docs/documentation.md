# Dropbox to Google Drive Migration Tool Documentation

This document provides a comprehensive overview of the Dropbox to Google Drive Migration Tool, including its features, usage, and configuration.

## 1. Introduction

This command-line utility is designed to help users migrate their files and folders from a Dropbox account to a Google Drive account. It is built to be robust and user-friendly, with features like resumable migrations, conflict resolution, and different modes of operation to suit various user needs.

## 2. Installation and Configuration

### 2.1. Prerequisites

*   Python 3.6+
*   Pip (Python package installer)

### 2.2. Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd dropbox-migration-tool
    ```

2.  **Install dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```

### 2.3. Configuration

The tool requires API credentials for both Dropbox and Google Drive to function.

#### 2.3.1. Getting Credentials

##### Dropbox
1. Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps) and create a new app.
2. Choose the "Scoped access" API and "Full Dropbox" access.
3. In the "Permissions" tab, ensure the following scopes are checked: `files.content.read`, `files.content.write`, and `files.metadata.read`.
4. From the "Settings" tab, get your "App key" and "App secret".

##### Google Drive
1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2. Enable the "Google Drive API".
3. Go to "Credentials", click "Create Credentials", and choose "OAuth client ID". Select "Desktop app".
4. Download the credentials JSON file, rename it to `client_secrets.json`, and place it in the project's root directory.

#### 2.3.2. Providing Credentials to the Tool

*   **Dropbox**: Provide your Dropbox API key and secret in either `config.ini` (by renaming the template) or as environment variables (`DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`).
*   **Google Drive**: The tool will automatically use the `client_secrets.json` file. Upon first run, it will generate a `google_token.json` file to store your user-specific authentication token.

## 3. Usage

The tool is run from the command line from the root of the project directory.

### 3.1. Standard Migration

To run a full migration, the tool will first present a summary of the files to be migrated and ask for your confirmation.

```bash
python3 -m src.main
```

### 3.2. Command-Line Options

*   `--dry_run`: Generates a detailed plan of which files will be migrated from source to destination without performing any actual operations.
*   `--interactive`: Prompts for confirmation before migrating each folder.
*   `--src <path>`: Specifies a source directory in Dropbox. Only the contents of this directory will be migrated.
*   `--dest <path>`: Specifies a destination directory in Google Drive.
*   `--limit <number>`: Restricts the migration to a specific number of files. This works for both standard migrations and dry runs.

### 3.3. Examples

*   **Perform a dry run of the first 50 files**:
    ```bash
    python3 -m src.main --dry_run --limit 50
    ```
*   **Migrate a specific Dropbox folder to a specific Google Drive folder**:
    ```bash
    python3 -m src.main --src "/My Dropbox Folder" --dest "My Google Drive Folder/Backup"
    ```

## 4. Features

### 4.1. Resumable Migrations

The tool keeps track of its progress in a `migration_state.json` file. If the migration is interrupted, you can simply run the command again, and it will pick up where it left off.

### 4.2. Conflict Resolution

*   **Folders**: If a folder with the same name already exists in the destination, the tool will use the existing folder.
*   **Files**: If a file with the same name already exists, you will be prompted to choose to **overwrite**, **rename**, or **skip** it. You can also choose to apply your decision to all subsequent conflicts in the same session.

### 4.3. Robust Error Handling

The tool automatically handles common API errors, expired authentication tokens, and files that fail to transfer. A summary of any failed files is provided at the end of the session.

## 5. The State File

The `migration_state.json` file is crucial for the tool's operation. It contains:

*   `migrated_files`: A list of the full paths of all files that have been successfully migrated.
*   `skipped_files`: A list of files that you chose to skip.
*   `migrated_folders`: A mapping of Dropbox folder paths to their corresponding Google Drive folder IDs.
*   `skipped_folders`: A list of folders that you chose to skip during an interactive run.

It is recommended not to edit this file manually.
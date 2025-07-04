# Dropbox to Google Drive Migration Tool Documentation

This document provides a comprehensive overview of the Dropbox to Google Drive Migration Tool, including its features, usage, and configuration.

## 1. Introduction

This command-line utility is designed to help users migrate their files and folders from a Dropbox account to a Google Drive account. It is built to be robust, with features like resumable migrations, conflict resolution, and different modes of operation to suit various user needs.

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
    pip install -r requirements.txt
    ```

### 2.3. Configuration

The tool requires API credentials for both Dropbox and Google Drive to function.

#### 2.3.1. Getting Credentials

##### Dropbox
1. Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps) and create a new app.
2. Choose the "Scoped access" API.
3. Select "Full Dropbox" access.
4. Give your app a unique name.
5. Once the app is created, go to the "Permissions" tab and make sure the following permissions are checked:
    - `files.content.read`
    - `files.content.write`
    - `files.metadata.read`
6. Go to the "Settings" tab and find your "App key" and "App secret".

##### Google Drive
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Go to "APIs & Services" > "Enabled APIs & services" and click "ENABLE APIS AND SERVICES".
4. Search for "Google Drive API" and enable it.
5. Go to "APIs & Services" > "Credentials".
6. Click "Create Credentials" and choose "OAuth client ID".
7. Select "Desktop app" for the application type.
8. After creation, download the JSON file. Rename it to `google_credentials.json` and place it in the root of this project.

#### 2.3.2. Providing Credentials to the Tool

##### Dropbox
You can provide your Dropbox API key and secret in one of two ways:

*   **Configuration File (Recommended):**
    1.  Rename `config.ini.template` to `config.ini`.
    2.  Open `config.ini` and fill in your `app_key` and `app_secret`.

*   **Environment Variables:**
    Set the following environment variables in your terminal:
    ```bash
    export DROPBOX_APP_KEY='YOUR_APP_KEY'
    export DROPBOX_APP_SECRET='YOUR_APP_SECRET'
    ```
    *Note: Environment variables will override the values in `config.ini`.*

##### Google Drive
The tool will automatically use the `google_credentials.json` file you created.

## 3. Usage

The tool is run from the command line:

```bash
python3 -m src.main [OPTIONS]
```

### 3.1. Standard Migration

To run a full migration of all your files and folders, simply run:

```bash
python3 -m src.main
```

### 3.2. Command-Line Options

*   `--dry_run`: Use this flag to generate a plan of files to be migrated without performing the migration. The tool will print a list of source and destination paths.

    ```bash
    python3 -m src.main --dry_run
    ```

*   `--interactive`: Use this flag to run the migration in an interactive mode. The tool will pause before migrating each folder, list the files inside it, and ask for your confirmation to proceed, skip, or quit.

    ```bash
    python3 -m src.main --interactive
    ```

    *Note: `--dry_run` and `--interactive` cannot be used at the same time.*

*   `--src <path>`: Specifies a source directory in Dropbox. Only the contents of this directory will be migrated. For example, to migrate only the files in your Dropbox `/Apps/MyApp` folder, you would use:
    ```bash
    python3 -m src.main --src /Apps/MyApp
    ```

*   `--dest <path>`: Specifies a destination directory in Google Drive. Files will be migrated to this directory, preserving the source directory structure. For example, to migrate your files to a folder named `MyDropboxBackup` in your Google Drive, you would use:
    ```bash
    python3 -m src.main --dest MyDropboxBackup
    ```
    You can also specify a nested path:
    ```bash
    python3 -m src.main --dest Backups/MyDropboxBackup
    ```

    You can use `--src` and `--dest` together to migrate a specific Dropbox folder to a specific Google Drive folder.

## 4. Features

### 4.1. Resumable Migrations

The tool keeps track of its progress in a `migration_state.json` file. If the migration is interrupted for any reason, you can simply run the command again, and it will pick up where it left off, skipping any files and folders that have already been successfully migrated.

### 4.2. Conflict Resolution

*   **Folders**: If a folder with the same name already exists in the destination, the tool will use the existing folder instead of creating a new one, effectively merging the contents.
*   **Files**: If a file with the same name already exists, you will be prompted to choose one of three options:
    1.  **Overwrite**: Replace the existing file.
    2.  **Rename**: Upload the new file with a `(1)` suffix.
    3.  **Skip**: Do not migrate the file.

### 4.3. Robust Error Handling

The tool automatically handles common API errors, such as rate limiting. If a request fails with a retryable error, the tool will wait for a short period and then try again, using an exponential backoff strategy to avoid overwhelming the API.

## 5. The State File

The `migration_state.json` file is crucial for the tool's operation. It contains:

*   `migrated_files`: A list of the full paths of all files that have been successfully migrated.
*   `migrated_folders`: A mapping of Dropbox folder paths to their corresponding Google Drive folder IDs.
*   `skipped_folders`: A list of folders that you chose to skip during an interactive run.

It is recommended not to edit this file manually unless you need to reset the migration state.

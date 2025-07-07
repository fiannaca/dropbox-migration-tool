# Dropbox to Google Drive Migration Utility

A robust command-line tool to migrate files and folders from Dropbox to Google Drive, with a focus on reliability and a user-friendly experience.

This tool was an experiment in using the Gemini CLI for rapid software development. All code in this repository was written by the Gemini CLI using Gemini 2.5 Pro.

## Key Features

- **Resumable Migrations**: If the script is interrupted, it can be restarted and will automatically resume where it left off, skipping already transferred files.
- **Intelligent Conflict Resolution**: If a file already exists in Google Drive, you can choose to **overwrite** it, **rename** it, or **skip** it. The tool can also remember your choice for all future conflicts in the same session.
- **Targeted Migrations**: Use the `--src` and `--dest` flags to migrate specific folders to a chosen location in Google Drive.
- **Dry Runs**: Use the `--dry_run` flag to see a plan of what will be migrated without actually transferring any files.
- **Interactive Mode**: Use the `--interactive` flag to be prompted for confirmation before each folder is migrated.
- **Robust Error Handling**: The tool gracefully handles common API errors, expired authentication tokens, and files that fail to transfer, providing a summary of any failed files at the end of the session.

## Setup

1.  **Install Dependencies**:

    ```bash
    pip3 install -r requirements.txt
    ```

2.  **Configure Credentials**

    You'll need to get API credentials from both Dropbox and Google.

    ### Dropbox

    1.  Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps) and create a new app.
    2.  Choose the "Scoped access" API and "Full Dropbox" access.
    3.  In the "Permissions" tab, ensure the following scopes are checked: `files.content.read`, `files.content.write`, and `files.metadata.read`.
    4.  From the "Settings" tab, get your "App key" and "App secret".

    ### Google Drive

    1.  **Create a Project**: Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
    2.  **Enable the API**: In your new project, go to **APIs & Services > Enabled APIs & services** and click **ENABLE APIS AND SERVICES**. Search for "Google Drive API" and enable it.
    3.  **Configure the OAuth Consent Screen**:
        - Go to **APIs & Services > OAuth consent screen**.
        - Choose **External** for the user type and click **Create**.
        - Fill in the required app information (app name, user support email).
        - On the "Scopes" page, click **Add or Remove Scopes**. Find the scope for the Google Drive API (`.../auth/drive`) and add it.
        - On the "Test users" page, add the email addresses of any users who will be testing the application while it is in "test mode".
    4.  **Create Credentials**:
        - Go to **APIs & Services > Credentials**.
        - Click **Create Credentials** and choose **OAuth client ID**.
        - Select **Desktop app** for the application type.
        - After creation, download the JSON file. Rename it to `client_secrets.json` and place it in the root directory of this project.

3.  **Configure the Tool**

    Provide your Dropbox API credentials using either a configuration file or environment variables.

    - **Config File (Recommended)**: Rename `config.ini.template` to `config.ini` and add your app key and secret.
    - **Environment Variables**: Set `DROPBOX_APP_KEY` and `DROPBOX_APP_SECRET`. These will override the config file.

## Usage

The tool is run from the command line from the root of the project directory.

### Standard Migration

To run a full migration of all your files, the tool will first present a summary of the files to be migrated and ask for your confirmation.

```bash
python3 -m src.main
```

### Command-Line Options

- `--dry_run`: Generates a detailed plan of which files will be migrated from source to destination without performing any actual operations.
- `--interactive`: Prompts for confirmation before migrating each folder.
- `--src <path>`: Specifies a source directory in Dropbox. Only the contents of this directory will be migrated.
- `--dest <path>`: Specifies a destination directory in Google Drive.
- `--limit <number>`: Restricts the migration to a specific number of files. This works for both standard migrations and dry runs.

### Examples

- **Perform a dry run of the first 50 files**:
  ```bash
  python3 -m src.main --dry_run --limit 50
  ```
- **Migrate a specific Dropbox folder to a specific Google Drive folder**:
  ```bash
  python3 -m src.main --src "/My Dropbox Folder" --dest "My Google Drive Folder/Backup"
  ```
- **Migrate a shared folder**:
  ```bash
  python3 -m src.main --src "ns:1234567890" --dest "My Shared Folder Backup"
  ```

## Migrating Shared Folders

To migrate a shared folder, you need to use its unique **Namespace ID**.

1.  Go to the Dropbox website and open the shared folder.
2.  The URL in your browser's address bar will look something like this: `https://www.dropbox.com/work/your-team-name/browse/g-drive-migration/ns:1234567890`.
3.  The Namespace ID is the part of the URL that starts with `ns:`. In this example, it is `ns:1234567890`.
4.  Use this ID as the value for the `--src` flag.

## Troubleshooting

- **Authentication Errors**: If you see an `AuthError` or `RefreshError`, your authentication token has likely expired. The tool will automatically attempt to re-authenticate you. If this fails, you may need to delete the `dropbox_credentials.json` or `google_token.json` file and run the tool again to go through the authentication flow.
- **File Migration Failures**: If a file fails to migrate due to an API error or other issue, it will be skipped, and its path will be listed in the final summary report. You can review the `migration.log` file for more detailed error messages.
- **Special Characters in Filenames**: The tool is designed to handle filenames with special characters like single quotes, double quotes, and others by sanitizing them for local storage and correctly escaping them for API calls. If you encounter an issue with a specific filename, please check the log for details.

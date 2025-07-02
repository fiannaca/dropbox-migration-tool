# Dropbox to Google Drive Migration Utility

This utility helps you migrate your files and folders from Dropbox to Google Drive.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Credentials**

    You'll need to get API credentials from both Dropbox and Google.

    ### Dropbox
    1. Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps) and create a new app.
    2. Choose the "Scoped access" API.
    3. Select "Full Dropbox" access.
    4. Give your app a unique name.
    5. Once the app is created, go to the "Permissions" tab and make sure the following permissions are checked:
        - `files.content.read`
        - `files.content.write`
        - `files.metadata.read`
    6. Go to the "Settings" tab and find your "App key" and "App secret". You will need these for the `main.py` file.

    ### Google Drive
    1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
    2. Create a new project.
    3. Go to "APIs & Services" > "Enabled APIs & services" and click "ENABLE APIS AND SERVICES".
    4. Search for "Google Drive API" and enable it.
    5. Go to "APIs & Services" > "Credentials".
    6. Click "Create Credentials" and choose "OAuth client ID".
    7. Select "Desktop app" for the application type.
    8. After creation, download the JSON file. Rename it to `google_credentials.json` and place it in the root of this project.

3.  **Configure the Tool**

    There are two ways to provide your Dropbox API credentials:

    **Option 1: Configuration File (Recommended)**
    1.  Rename the `config.ini.template` file to `config.ini`.
    2.  Open `config.ini` and replace the placeholder values for `app_key` and `app_secret` with the credentials you obtained from Dropbox.

    **Option 2: Environment Variables**
    You can also set the following environment variables:
    ```bash
    export DROPBOX_APP_KEY='YOUR_APP_KEY'
    export DROPBOX_APP_SECRET='YOUR_APP_SECRET'
    ```
    The tool will prioritize environment variables if they are set.

4.  **Run the migration:**
    ```bash
    python3 src/main.py
    ```

    **Optional Flags:**
    *   `--test_run`: Migrates the first 10 files, pausing for confirmation after each one.
    *   `--interactive`: Prompts for confirmation before migrating each folder.

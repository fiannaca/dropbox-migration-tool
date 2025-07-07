# Specification: Dropbox to Google Drive Migration Utility

## Summary

The goal of this project is to create a command-line utility that facilitates the migration of files and folders from a user's Dropbox account to their Google Drive account. The tool will use OAuth 2.0 to securely authenticate with both services. It will recursively scan the Dropbox account, preserving the directory structure, and upload the files to Google Drive. The utility will be designed to be robust and resumable, allowing the user to continue a migration that has been interrupted.

## Steps

1.  **API Research**:
    *   Thoroughly read the Dropbox API documentation, with a focus on file and folder operations.
    *   Thoroughly read the Google Drive API documentation, with a focus on file and folder operations.
    *   Identify the specific API endpoints and scopes required for the migration.

2.  **Project Setup**:
    *   Initialize a new project repository.
    *   Choose a programming language and package manager (e.g., Python with Pip, Node.js with NPM).
    *   Create a basic project structure (`src`, `docs`, `tests`).

3.  **Authentication**:
    *   Implement the OAuth 2.0 authorization flow for the Dropbox API.
    *   Implement the OAuth 2.0 authorization flow for the Google Drive API.
    *   Securely store and manage API credentials and user access/refresh tokens.

4.  **Dropbox Client**:
    *   Develop a module to interact with the Dropbox API.
    *   Implement a function to list all files and folders recursively.
    *   Implement a function to download a single file.

5.  **Google Drive Client**:
    *   Develop a module to interact with the Google Drive API.
    *   Implement a function to create a folder.
    *   Implement a function to upload a file into a specified folder.

6.  **Migration Logic**:
    *   Create the core logic that orchestrates the migration.
    *   Traverse the Dropbox file tree.
    *   For each Dropbox folder, create a corresponding folder in Google Drive.
    *   For each Dropbox file, download it and upload it to the correct folder in Google Drive.

7.  **State Management**:
    *   Implement a mechanism to track the migration progress (e.g., using a local JSON file or a simple database).
    *   Before migrating an item, check if it has already been successfully migrated.
    *   Update the state file after each successful file or folder migration.

8.  **User Interface (CLI)**:
    *   Build a command-line interface.
    *   Create commands to:
        *   Initiate the authentication process for both services.
        *   Start the migration process.
        *   Show migration status and progress.

9.  **Error Handling and Logging**:
    *   Implement comprehensive error handling for API requests, network issues, and file I/O.
    *   Add logging to a file to help with debugging.

10.  **Documentation**:
    *   Write a `README.md` file with clear instructions on how to:
        *   Set up the project.
        *   Obtain API keys from both Dropbox and Google.
        *   Run the utility.

## Acceptance Criteria

1.  A user can successfully authorize the tool to access their Dropbox and Google Drive accounts.
2.  The tool replicates the complete folder hierarchy from Dropbox to Google Drive.
3.  All files are successfully transferred from Dropbox to their corresponding new folders in Google Drive.
4.  File content remains unchanged after the transfer.
5.  If the migration is interrupted, it can be resumed without re-transferring files that were already completed.
6.  The tool correctly handles empty folders.
7.  The tool provides clear progress updates to the user during the migration.
8.  Errors during the migration of a specific file/folder are logged, and the tool attempts to continue with the rest of the migration.
9.  The `README.md` file provides sufficient detail for a new user to get the tool running.
10. The tool correctly handles naming conflicts.

## Conflict Resolution

When a file or folder with the same name already exists in the destination Google Drive folder, the following strategies will be used:

*   **Folders**: If a folder with the same name exists, the tool will assume it is the same folder and use it as the destination for files within that folder. This effectively merges the contents.
*   **Files**: If a file with the same name exists, the user will be prompted to choose one of the following options:
    1.  **Overwrite**: Replace the existing file in Google Drive with the one from Dropbox.
    2.  **Rename**: Upload the Dropbox file but add a suffix to the name (e.g., `filename (1).txt`).
    3.  **Skip**: Do not migrate the file.

## Test Run Feature

To allow users to verify the migration process on a small scale before committing to a full migration, a `--test_run` flag is available. When this flag is used, the tool will:

1.  Identify the first 10 files that have not yet been migrated.
2.  Migrate these files one by one.
3.  After each successful file transfer, it will pause and wait for the user to press Enter before proceeding to the next file.
4.  The state of these test transfers will be saved, so they are not re-migrated during a subsequent full run.

## Interactive Mode

For users who want more control over the migration process, an `--interactive` flag is available. When this flag is used, the tool will:

1.  Before migrating each folder, pause and list the files that are about to be migrated within that folder.
2.  Wait for the user to choose one of the following options:
    *   **Enter**: Proceed with migrating the folder.
    *   **s**: Skip the current folder and all its contents.
    *   **Esc**: Quit the migration immediately.
3.  Skipped folders will be recorded in the state file to ensure they are not re-migrated on subsequent runs.
4.  If the user quits, the current state of the migration will be saved.
5.  The `--interactive` and `--test_run` flags are mutually exclusive and will result in an error if used together.

## Advanced Error Handling

To handle API rate limits and other transient network errors, the application will implement an exponential backoff strategy.

*   **Exponential Backoff**: When an API request fails with a rate limit error (e.g., HTTP 429) or a server-side error (e.g., HTTP 5xx), the tool will automatically:
    1.  Wait for a short, randomized interval.
    2.  Retry the request.
    3.  If the request fails again, it will double the waiting period and repeat, up to a maximum number of retries.
*   **Implementation**: This will be implemented as a reusable Python decorator that can be applied to any function making an API call.

## Directory Listing Feature

To help users identify the correct paths for the `--src` flag, a `--ls` flag is available. When this flag is used, the tool will:

1.  List the files and folders in the specified `--src` directory (or the root if no source is provided).
2.  The listing will not be recursive.
3.  The tool will then exit without performing any migration.


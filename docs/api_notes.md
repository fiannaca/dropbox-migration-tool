# API Research Notes

## Dropbox API

*   **Authentication**: OAuth 2.0
*   **Key Scopes**: `files.content.write`, `files.content.read`
*   **Endpoints**:
    *   `POST /files/create_folder_v2`: To create new folders.
    *   `POST /files/upload`: For uploading files up to 150 MB.
    *   `POST /files/upload_session/start`, `POST /files/upload_session/append_v2`, `POST /files/upload_session/finish`: For uploading large files in chunks.
    *   `POST /files/list_folder`: To list the contents of a folder.
    *   `POST /files/list_folder/continue`: To paginate through folder contents.
    *   `POST /files/download`: To download files.
*   **Libraries**: The official `dropbox` Python library is available.

## Google Drive API

*   **Authentication**: OAuth 2.0
*   **Key Scopes**: `https://www.googleapis.com/auth/drive.file` (to create/upload files), `https://www.googleapis.com/auth/drive.readonly` (to list existing files/folders to avoid duplicates).
*   **Upload Types**:
    *   **Simple upload**: For small files (<= 5MB) without metadata.
    *   **Multipart upload**: For small files (<= 5MB) with metadata.
    *   **Resumable upload**: Recommended for large files and for robustness against network interruptions. This is the best fit for our tool.
*   **Libraries**: The `google-api-python-client` library in conjunction with `google-auth-oauthlib` for authentication.

## Plan of Action

1.  Use the `dropbox` library to list all files and folders recursively from the user's Dropbox account.
2.  For each Dropbox folder, use the Google Drive API to create a corresponding folder. We'll need to keep a mapping of Dropbox folder paths to Google Drive folder IDs.
3.  For each file, use the resumable upload feature of the Google Drive API to upload it to the correct destination folder.
4.  Store the access and refresh tokens for both services securely on the user's local machine.

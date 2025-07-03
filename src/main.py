import logging
import argparse
import os
import configparser
import sys
from src.dropbox_auth import get_access_token as get_dropbox_token, save_credentials as save_dropbox_credentials, load_credentials as load_dropbox_credentials
from src.google_drive_auth import get_credentials as get_google_credentials
from src.migration import Migration
from src.logger_config import setup_logger

def get_config():
    """
    Reads configuration from environment variables or config.ini.
    """
    config = configparser.ConfigParser()
    config.read('config.ini')

    dropbox_app_key = os.environ.get('DROPBOX_APP_KEY') or config.get('dropbox', 'app_key', fallback=None)
    dropbox_app_secret = os.environ.get('DROPBOX_APP_SECRET') or config.get('dropbox', 'app_secret', fallback=None)
    
    return dropbox_app_key, dropbox_app_secret

def main(argv=None):
    """
    Main function to orchestrate the migration.
    """
    parser = argparse.ArgumentParser(description="Migrate files from Dropbox to Google Drive.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--test_run', action='store_true', help='Run a test migration of the first 10 files.')
    group.add_argument('--interactive', action='store_true', help='Run in interactive mode, confirming each folder.')
    parser.add_argument('--src', type=str, default=None, help='The source directory path in Dropbox.')
    parser.add_argument('--dest', type=str, default=None, help='The destination directory path in Google Drive.')
    args = parser.parse_args(argv)

    setup_logger()
    
    dropbox_app_key, dropbox_app_secret = get_config()
    if not dropbox_app_key or not dropbox_app_secret:
        logging.error("Dropbox API credentials not found. Please set them in config.ini or as environment variables.")
        sys.exit(1)

    # --- Dropbox Authentication ---
    dropbox_token = load_dropbox_credentials()
    if not dropbox_token:
        logging.info("Authenticating with Dropbox...")
        dropbox_token = get_dropbox_token(dropbox_app_key, dropbox_app_secret)
        if dropbox_token:
            save_dropbox_credentials(dropbox_token)
            logging.info("Dropbox authentication successful.")
        else:
            logging.error("Dropbox authentication failed. Exiting.")
            return

    # --- Google Drive Authentication ---
    logging.info("Authenticating with Google Drive...")
    google_creds = get_google_credentials(credentials_path='google_credentials.json')
    if google_creds:
        logging.info("Google Drive authentication successful.")
    else:
        logging.error("Google Drive authentication failed. Exiting.")
        return

    # --- Start Migration ---
    migration = Migration(dropbox_token, google_creds, src_path=args.src, dest_path=args.dest)
    migration.start(test_run=args.test_run, interactive=args.interactive)

if __name__ == '__main__':
    main()

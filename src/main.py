import logging
import argparse
import os
import configparser
import sys
import dropbox
from google.auth.exceptions import RefreshError
from src.dropbox_auth import get_access_token as get_dropbox_token, save_credentials as save_dropbox_credentials, load_credentials as load_dropbox_credentials, CREDENTIALS_FILE as DROPBOX_CREDENTIALS_FILE
from src.google_drive_auth import get_credentials as get_google_credentials, TOKEN_PATH as GOOGLE_TOKEN_PATH
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
    parser.add_argument('--dry_run', action='store_true', help='Generate a plan of files to be migrated without performing the migration.')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode, confirming each folder.')
    parser.add_argument('--src', type=str, default=None, help='The source directory path in Dropbox.')
    parser.add_argument('--dest', type=str, default=None, help='The destination directory path in Google Drive.')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of lines printed in a test run.')
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
    google_creds = get_google_credentials()
    if google_creds:
        logging.info("Google Drive authentication successful.")
    else:
        logging.error("Google Drive authentication failed. Exiting.")
        return

    # --- Start Migration ---
    while True:
        try:
            migration = Migration(dropbox_token, google_creds, src_path=args.src, dest_path=args.dest)
            migration.start(dry_run=args.dry_run, interactive=args.interactive, limit=args.limit)
            break # Exit the loop if migration completes successfully
        except dropbox.exceptions.AuthError as e:
            if 'expired_access_token' in str(e):
                logging.warning("Dropbox access token has expired. Attempting to re-authenticate.")
                if os.path.exists(DROPBOX_CREDENTIALS_FILE):
                    os.remove(DROPBOX_CREDENTIALS_FILE)
                
                dropbox_token = get_dropbox_token(dropbox_app_key, dropbox_app_secret)
                if dropbox_token:
                    save_dropbox_credentials(dropbox_token)
                    logging.info("Dropbox re-authentication successful. Resuming migration.")
                else:
                    logging.error("Dropbox re-authentication failed. Exiting.")
                    break
            else:
                logging.error(f"An unexpected Dropbox authentication error occurred: {e}")
                break
        except RefreshError:
            logging.warning("Google Drive access token has expired. Attempting to re-authenticate.")
            if os.path.exists(GOOGLE_TOKEN_PATH):
                os.remove(GOOGLE_TOKEN_PATH)
            
            google_creds = get_google_credentials()
            if google_creds:
                logging.info("Google Drive re-authentication successful. Resuming migration.")
            else:
                logging.error("Google Drive re-authentication failed. Exiting.")
                break
        except KeyboardInterrupt:
            logging.info("\nMigration interrupted by user.")
            migration.log_migration_summary()
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred during migration: {e}")
            break

if __name__ == '__main__':
    main()

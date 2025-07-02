import dropbox
import webbrowser
import json
import logging

def get_access_token(app_key, app_secret):
    """
    Authenticates with Dropbox and returns an access token.
    """
    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
    authorize_url = auth_flow.start()

    logging.info("1. Go to: " + authorize_url)
    logging.info("2. Click 'Allow' (you might have to log in first).")
    logging.info("3. Copy the authorization code.")
    webbrowser.open(authorize_url)
    auth_code = input("Enter the authorization code here: ").strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
        return oauth_result.access_token
    except Exception as e:
        logging.error('Error: %s' % (e,))
        return None

def save_credentials(access_token, file_path='dropbox_credentials.json'):
    """
    Saves the access token to a file.
    """
    with open(file_path, 'w') as f:
        json.dump({'access_token': access_token}, f)

def load_credentials(file_path='dropbox_credentials.json'):
    """
    Loads the access token from a file.
    """
    try:
        with open(file_path, 'r') as f:
            credentials = json.load(f)
            return credentials.get('access_token')
    except FileNotFoundError:
        return None

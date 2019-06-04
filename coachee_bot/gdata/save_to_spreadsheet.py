#!/usr/bin/python3.6
from pprint import pprint
from googleapiclient import discovery
import os
from oauth2client.file import Storage

import sys #required because files in parent folder
sys.path.append('../')
import config

import sys #required because files in parent folder
sys.path.append('../classes')
from dbhelper import DBHelper

db = DBHelper()
db_export = db.db_export()
db_export.insert(0,['msg_id', 'chat_id', 'first_name', 'action', 'msg', 'step', 'msg_created_at', 'type', 'language_code'])

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'notadiet'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

credentials = get_credentials()

service = discovery.build('sheets', 'v4', credentials=credentials)

# The ID of the spreadsheet to update.
spreadsheet_id = config.DB_SPREADSHEET_ID  # TODO: Update placeholder value.

batch_update_values_request_body = {
    # How the input data should be interpreted.
    'value_input_option': 'RAW',  # TODO: Update placeholder value.

    # The new values to apply to the spreadsheet.
    'data': [
      {
        "range": "Sheet1",
        "majorDimension": "ROWS",
        "values":  db_export
      }
      ]  # TODO: Update placeholder value.

    # TODO: Add desired entries to the request body.
}

request = service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_values_request_body)
response = request.execute()

# TODO: Change code below to process the `response` dict:
pprint(response)

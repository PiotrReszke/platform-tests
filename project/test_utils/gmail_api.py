import base64
import os
import time

from apiclient import discovery, errors
import httplib2
import oauth2client

from test_utils import config
from test_utils.logger import get_logger


SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'praca-email'
TEST_EMAIL = config.TEST_SETTINGS["TEST_EMAIL"]

logger = get_logger("gmail client")


def get_credentials():
    directory = os.path.dirname(__file__)
    credential_path = os.path.join(directory, 'gmail-code.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = oauth2client.tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def list_messages_matching_query(service, query=''):
    try:
        response = service.users().messages().list(userId=TEST_EMAIL, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=TEST_EMAIL, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        raise Exception("Can't get messages from {} - {}".format(TEST_EMAIL, error))


def get_message(service, msg_id):
    try:
        message = service.users().messages().get(userId=TEST_EMAIL, id=msg_id, format='raw').execute()
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def get_recent_message_to(to_email):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    start = time.time()
    time_frame = 16
    while time.time() - start < time_frame:
        message_list = (list_messages_matching_query(service, to_email))
        message_numb = len(message_list)
        logger.info("---- Getting messages from {} email address, there are {} messages to {} ----".format(TEST_EMAIL,
                                                                                                message_numb, to_email))
        if message_numb >= 2:
            return get_message(service, message_list[0].get('id'))['raw']
        time.sleep(3)
        raise TimeoutError("Can't find email message with code to {}".format(to_email))


def extract_code_from_message(message):
    b = base64.urlsafe_b64decode(message)
    c = b.decode()  # .replace('=3D', '=').replace('=\r\n', '')
    d = c.find('code=')
    if d != -1:
        d += len('code=')
        e = c[d:].find('&')
        code = (c[d:d + e])
        return code
    else:
        raise Exception("Can't find code in given message")


def get_code_from_gmail(email):
    message = get_recent_message_to(email)
    code = extract_code_from_message(message)
    return code



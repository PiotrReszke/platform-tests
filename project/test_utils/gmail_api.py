#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import base64
import os
import re

from apiclient import discovery, errors
import httplib2
import oauth2client

from . import config, get_logger


SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'secrets/client_secret.json'
APPLICATION_NAME = 'praca-email'
TEST_EMAIL = config.TEST_SETTINGS["TEST_EMAIL"]
INVITATION_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"

logger = get_logger("gmail client")


def get_query(username, email_subject=None):
    query = "to:{}".format(username, email_subject)
    if email_subject is not None:
        query += " subject:{}".format(email_subject)
    return query

def get_credentials():
    directory = os.path.dirname(__file__)
    credential_path = os.path.join(directory, 'secrets/gmail-code.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = oauth2client.tools.run_flow(flow, store)
        logger.info('Storing credentials to ' + credential_path)
    return credentials


def get_invitation_code(username):
    message_query = get_query(username)
    message_ids = list_messages_matching_query(TEST_EMAIL, message_query)
    if len(message_ids) != 1:
        raise AssertionError("There are {} e-mail messages instead of 1".format(len(message_ids)))
    message = get_message(message_ids[0].get("id"))
    return extract_code_from_message(message[1])


def list_messages_matching_query(user_id, query=''):
    service = get_service()
    try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])
        return messages
    except errors.HttpError as error:
        raise Exception("Can't get messages from {} - {}".format(user_id, error))


def get_service():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    return service


def get_link_from_message(email_content):
    return re.findall(r'"(https?://[^\s]+)"', email_content)[0]


def get_message(id_msg):
    service = get_service()
    message = service.users().messages().get(userId="intel.data.tests@gmail.com", id=id_msg, format='full').execute()
    message_subject = message['payload']['headers'][12]['value']
    msg_str = base64.urlsafe_b64decode(message['payload']['body']['data'].encode('ASCII'))
    message_content = msg_str.decode("utf-8")
    return message_subject, message_content


def extract_code_from_message(message):
    start = message.find('code=')
    if start != -1:
        start += len('code=')
        end = message[start:].find('"')
        code = (message[start:start + end])
        return code
    else:
        raise Exception("Can't find code in given message: \n")

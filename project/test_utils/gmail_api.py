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
import time
from operator import itemgetter

from apiclient import discovery
import httplib2
import oauth2client
from retry import retry

from . import config, get_logger

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'secrets/client_secret.json'
APPLICATION_NAME = 'praca-email'
TEST_EMAIL = config.TEST_SETTINGS["TEST_EMAIL"]
INVITATION_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
INVITATION_LINK_PATTERN = r'"(https?://[^\s]+)"'

logger = get_logger("gmail client")


def _get_credentials():
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


def _get_service():
    credentials = _get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    return service


def get_query(recipient, email_subject=None):
    query = "to:{}".format(recipient)
    if email_subject is not None:
        query += " subject:{}".format(email_subject)
    return query


def _retrieve_message_ids_matching_query(user_id, query=''):
    service = _get_service()
    response = service.users().messages().list(userId=user_id, q=query).execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])
    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
        messages.extend(response['messages'])
    return [msg["id"] for msg in messages]


def get_messages(recipient, user_id=TEST_EMAIL, subject=None):
    query = get_query(recipient, subject)
    message_ids = _retrieve_message_ids_matching_query(user_id, query)
    service = _get_service()
    messages = []
    for message_id in message_ids:
        message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
        timestamp = message['internalDate']
        message_subject = message['payload']['headers'][12]['value']
        msg_str = base64.urlsafe_b64decode(message['payload']['body']['data'].encode('ASCII'))
        message_content = msg_str.decode("utf-8")
        messages.append({"subject": message_subject, "content": message_content, "timestamp": timestamp})
    return messages


@retry(AssertionError, tries=30, delay=2)
def wait_for_messages(recipient, user_id=TEST_EMAIL, subject=None, messages_number=1):
    messages = get_messages(recipient, user_id=user_id, subject=subject)
    assert len(messages) == messages_number
    return messages


def extract_code_from_message(message):
    pattern = r"(?<=code=)([a-z]|[0-9]|-)+"
    match = re.search(pattern, message)
    if match is None:
        raise AssertionError("Can't find code in given message: {}".format(message))
    return match.group()


def get_invitation_code(username):
    messages = wait_for_messages(recipient=username)
    return extract_code_from_message(messages[0]["content"])


def get_link_from_message(email_content):
    match = re.search(INVITATION_LINK_PATTERN, email_content)
    if match is None:
        raise AssertionError("Invitation link was not found in email content")
    return match.group()


def get_code_from_latest_message(username):
    time.sleep(30)
    messages = sorted(get_messages(recipient=username), key=itemgetter('timestamp'), reverse=True)
    return extract_code_from_message(messages[0]["content"])

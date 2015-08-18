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

from test_utils import get_logger


logger = get_logger("das calls")


APP_NAME = "das"


def api_get_das_requests(client, org_guids):
    """GET /rest/das/requests"""
    logger.debug("------------------ Get transfers ------------------")
    org_guids = ",".join(org_guids)
    return client.call(APP_NAME, "get_requests", orgs=org_guids)


def api_create_das_request(client, category=None, id=None, id_in_object_store=None, is_public=None, org_guid=None, source=None,
                           state=None, token=None, timestamps=None, title=None, user_id=None):
    """POST /rest/das/requests"""
    logger.debug("------------------ Create a transfer ------------------")
    body_keys = ["category", "id", "idInObjectStore", "publicRequest", "orgUUID", "source", "state", "token",
                 "timestamps", "title", "userId"]
    values = [category, id, id_in_object_store, is_public, org_guid, source, state, token, timestamps, title, user_id]
    body = {key: val for key, val in zip(body_keys, values) if val is not None}
    return client.call(APP_NAME, "create_request", body=body)


def api_get_das_request(client, request_id):
    """GET /rest/das/requests/{request_id}"""
    logger.debug("------------------ Get transfer {} ------------------".format(request_id))
    return client.call(APP_NAME, "get_request", request_id=request_id)


def api_delete_das_request(client, request_id):
    """DELETE /rest/das/requests/{request_id}"""
    logger.debug("------------------ Delete transfer {} ------------------".format(request_id))
    return client.call(APP_NAME, "delete_request", request_id=request_id)

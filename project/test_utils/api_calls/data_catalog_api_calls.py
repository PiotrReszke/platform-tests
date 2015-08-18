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

import json

from test_utils import get_logger


logger = get_logger("data-catalog calls")
APP_NAME = "data-catalog"


def api_get_datasets(client, org_guid_list, query="", filters=None, size=100, time_from=0,
                     only_private=None, only_public=None):
    """GET /rest/datasets"""
    logger.debug("------------------ Get list of data sets in orgs {} ------------------".format(org_guid_list))
    filters = filters or []
    params = {
        "orgs": ",".join(org_guid_list),
        "query": json.dumps({"query": query, "filters": filters, "size": size, "from": time_from})
    }
    if only_private:
        params["onlyPrivate"] = only_private
    if only_public:
        params["onlyPublic"] = only_public
    return client.call(APP_NAME, "search_datasets", **params)


def api_get_dataset(client, entry_id):
    """GET /rest/datasets/{entry_id}"""
    logger.debug("------------------ Get data set {} ------------------".format(entry_id))
    raise NotImplementedError("Please add a schema for this method in data_catalog_swagger.json")


def api_delete_dataset(client, entry_id):
    """DELETE /rest/datasets/{entry_id}"""
    logger.debug("------------------ Delete data set {} ------------------".format(entry_id))
    raise NotImplementedError("Please add a schema for this method in data_catalog_swagger.json")


def api_update_dataset(client, entry_id, creation_time=None, target_uri=None, category=None, format=None,
                       record_count=None, is_public=None, org_guid=None, source_uri=None, size=None, data_sample=None,
                       title=None):
    """POST /rest/datasets/{entry_id}"""
    logger.debug("------------------ Update data set {} ------------------".format(entry_id))
    values = [creation_time, target_uri, category, format, record_count, is_public, org_guid, source_uri, size,
              data_sample, title]
    body_keys = ["creationTime", "targetUri", "category", "format", "recordCount", "isPublic", "orgUUID", "sourceUri",
                 "size", "dataSample", "title"]
    body = {k: v for k, v in zip(body_keys, values) if v is not None}
    raise NotImplementedError("Please add a schema for this method in data_catalog_swagger.json")


def api_put_dataset_in_index(client, entry_id, creation_time=None, target_uri=None, category=None, format=None,
                             record_count=None, is_public=None, org_guid=None, source_uri=None, size=None,
                             data_sample=None, title=None):
    """PUT /rest/datasets/{entry_id}"""
    logger.debug("------------------ Put data set {} in index ------------------".format(entry_id))
    values = [creation_time, target_uri, category, format, record_count, is_public, org_guid, source_uri, size,
              data_sample, title]
    body_keys = ["creationTime", "targetUri", "category", "format", "recordCount", "isPublic", "orgUUID", "sourceUri",
                 "size", "dataSample", "title"]
    body = {k: v for k, v in zip(body_keys, values) if v is not None}
    raise NotImplementedError("Please add a schema for this method in data_catalog_swagger.json")


def api_get_dataset_count(client, org_guid_list, only_private, only_public):
    """GET /rest/datasets/count"""
    logger.debug("------------------ Get data set count in orgs ------------------".format(org_guid_list))
    raise NotImplementedError("Please add a schema for this method in data_catalog_swagger.json")

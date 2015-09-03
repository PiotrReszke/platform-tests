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

import functools

from test_utils import platform_api_calls as api, get_logger


logger = get_logger("dataset")


@functools.total_ordering
class DataSet(object):

    COMPARABLE_ATTRIBUTES = ["category", "creation_time", "data_sample", "format", "is_public", "id",
                             "org_guid", "record_count", "size", "source", "target_uri", "title"]

    def __init__(self, category=None, creation_time=None, data_sample=None, format=None, id=None, is_public=None,
                 org_guid=None, record_count=None, size=None, source_uri=None, target_uri=None, title=None):
        self.category, self.creation_time, self.data_sample, self.format = category, creation_time, data_sample, format
        self.is_public, self.id, self.record_count, self.size = is_public, id, record_count, size
        self.source_uri, self.target_uri, self.title, self.org_guid = source_uri, target_uri, title, org_guid

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{0} (title={1}, id={2})".format(self.__class__.__name__, self.title, self.id)

    @classmethod
    def _from_api_response(cls, data):
        return cls(id=data["id"], category=data["category"], title=data["title"], format=data["format"],
                   creation_time=data["creationTime"], is_public=data["isPublic"], org_guid=data["orgUUID"],
                   data_sample=data["dataSample"], record_count=data["recordCount"], size=data["size"],
                   source_uri=data["sourceUri"], target_uri=data["targetUri"])

    @classmethod
    def api_get_list(cls, org_list, query="", filters=(), size=100, time_from=0, client=None):
        return cls.api_get_list_and_metadata(org_list, query, filters, size, time_from, client)["data_sets"]

    @classmethod
    def api_get_list_and_metadata(cls, org_list, query="", filters=(), size=100, time_from=0, client=None):
        org_guids = [org.guid for org in org_list]
        response = api.api_get_datasets(org_guids, query, filters, size, time_from, client=client)
        return {
            "categories": response["categories"],
            "formats": response["formats"],
            "total": response["total"],
            "data_sets": [cls._from_api_response(data) for data in response["hits"]]
        }

    @classmethod
    def api_get_matching_to_transfer(cls, org_list, transfer_title, client=None):
        """Return dataset whose title matches transfer_title or return None if such dataset is not found."""
        datasets = cls.api_get_list(org_list=org_list, client=client)
        return next((ds for ds in datasets if ds.title == transfer_title), None)

    @classmethod
    def api_get(cls, data_set_id, client=None):
        return cls.api_get_with_metadata(data_set_id, client)["data_set"]

    @classmethod
    def api_get_with_metadata(cls, data_set_id, client=None):
        response = api.api_get_dataset(data_set_id, client=client)
        return {
            "index": response["_index"],
            "found": response["found"],
            "type": response["_type"],
            "version": response["_version"],
            "data_set": cls._from_api_response(response["_source"])
        }

    def publish_in_hive(self, client=None):
        return api.api_publish_dataset(category=self.category, creation_time=self.creation_time,
                                       data_sample=self.data_sample, format=self.format, is_public=self.is_public,
                                       org_guid=self.org_guid, record_count=self.record_count, size=self.size,
                                       source_uri=self.source_uri, target_uri=self.target_uri, title=self.title,
                                       client=client)


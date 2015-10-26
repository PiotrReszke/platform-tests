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
import json

from test_utils import platform_api_calls as api, cloud_foundry as cf

__all__ = ["ServiceType"]


@functools.total_ordering
class ServiceType(object):
    """Otherwise known as broker"""

    COMPARABLE_ATTRIBUTES = ["guid", "label", "description", "tags", "space_guid", "is_active", "display_name"]

    def __init__(self, label, guid=None, description=None, tags=None, space_guid=None, is_active=None,
                 display_name=None, service_plans=None):
        self.guid, self.label, self.description, self.display_name = guid, label, description, display_name
        self.tags, self.space_guid, self.is_active = tags, space_guid, is_active
        self.service_plans = service_plans

    def __repr__(self):
        return "{0} (guid={1}, label={2})".format(self.__class__.__name__, self.guid, self.label)

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.guid < other.guid

    @property
    def service_plan_guids(self):
        return [sp["guid"] for sp in self.service_plans]

    @classmethod
    def api_get_list_from_marketplace(cls, space_guid, client=None):
        response = api.api_get_marketplace_services(space_guid=space_guid, client=client)
        return [cls._from_details(space_guid, data) for data in response]

    @classmethod
    def api_get(cls, space_guid, service_guid, client=None):
        response = api.api_get_service(service_guid=service_guid, client=client)
        return cls._from_details(space_guid, response)

    @classmethod
    def _from_details(cls, space_guid, data):
        metadata = data["metadata"]
        entity = data["entity"]
        display_name = None if entity["extra"] is None else json.loads(entity["extra"]).get("displayName")
        if display_name is None:
            display_name = entity["label"]
        service_plans = None
        if entity.get("service_plans") is not None:  # in cf response there are no service plans, but an url
            service_plans = [{"guid": sp["metadata"]["guid"], "name": sp["entity"]["name"]}
                             for sp in entity["service_plans"]]
        return cls(guid=metadata["guid"], label=entity["label"], description=entity["description"],
                   tags=entity["tags"], space_guid=space_guid, is_active=entity["active"],
                   display_name=display_name, service_plans=service_plans)

    @classmethod
    def cf_api_get_list_from_marketplace(cls, space_guid):
        cf_response = cf.cf_api_get_space_services(space_guid)
        return [cls._from_details(space_guid, data) for data in cf_response["resources"]]

    def api_get_service_plans(self, client=None):
        """Return a list of dicts with "guid" and "name" keys"""
        response = api.api_get_service_plans(self.label, client)
        service_plans = []
        for sp_data in response:
            name = sp_data["entity"]["name"]
            guid = sp_data["metadata"]["guid"]
            service_plans.append({"name": name, "guid": guid})
        self.service_plans = service_plans





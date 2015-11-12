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
import datetime

from test_utils import cloud_foundry as cf

__all__ = ["ServiceInstanceKey"]


@functools.total_ordering
class ServiceInstanceKey(object):

    COMPARABLE_ATTRIBUTES = ["guid", "name", "credentials", "service_instance_guid"]

    def __init__(self, guid, name, credentials, service_instance_guid):
        self.guid = guid
        self.name = name
        self.credentials = credentials or []
        self.service_instance_guid = service_instance_guid

    def __repr__(self):
        return "{0} (guid={1}, name={2})".format(self.__class__.__name__, self.guid, self.name)

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.guid < other.guid

    def __hash__(self):
        return hash((self.guid, self.name, self.credentias, self.service_instance_guid))

    @classmethod
    def cf_api_create(cls, service_instance_guid, service_key_name=None):
        service_key_name = service_key_name or "test_key_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        response = cf.cf_api_create_service_key(service_instance_guid, service_key_name)
        return cls(guid=response["metadata"]["guid"], name=response["entity"]["name"],
                   credentials=response["entity"]["credentials"],
                   service_instance_guid=response["entity"]["service_instance_guid"])


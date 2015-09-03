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

from test_utils import platform_api_calls as api



@functools.total_ordering
class EventSummary(object):
    def __init__(self, id, category=None, message=None, organization_id=None, source_id=None, source_name=None,
                 timestamp=None):
        self.id = id
        self.category = category
        self.message = message
        self.organization_id = organization_id
        self.source_id = source_id
        self.source_name = source_name
        self.timestamp = timestamp

    def __eq__(self, other):
        return (self.id == other.id and self.category == other.category and self.message == other.message and
                self.timestamp == other.timestamp)

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __hash__(self):
        return hash((self.id, self.category, self.message, self.timestamp))

    @classmethod
    def _get_events_from_response(cls, response):
        response = response.get("latestEvents") or response.get("events")
        events_list = []
        if response is not None:
            for event in response:
                events_list.append(cls(id=event["id"], category=event.get("category"), message=event.get("message"),
                                       organization_id=event.get("organizationId"), source_id=event.get("sourceId"),
                                       source_name=event.get("sourceName"), timestamp=event.get("timestamp")))
        return events_list

    @classmethod
    def api_get_latest_events(cls, client=None):
        response = api.api_get_latest_events(client)
        return cls._get_events_from_response(response)

    @classmethod
    def api_get_latest_events_from_org_metrics(cls, org_guid, client=None):
        response = api.api_get_org_metrics(org_guid, client)
        return cls._get_events_from_response(response)

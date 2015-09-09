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

logger = get_logger("external_tools")


@functools.total_ordering
class ExternalTools(object):
    def __init__(self, name=None, url=None, available=None):
        self.name = name
        self.url = url
        self.available = available

    def __eq__(self, other):
        return self.name == other.name and self.url == other.url and self.available == other.available

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash((self.name, self.url, self.available))

    @classmethod
    def api_get_external_tools(cls, client=None):
        response = api.api_get_external_tools(client)
        return cls._api_get_external_tools_from_response(response)

    @classmethod
    def _api_get_external_tools_from_response(cls, response):
        tools_list = []
        response = response.get('externalTools').get('list')
        if response is not None:
            for tool in response:
                tools_list.append(cls(name=tool.get('name'), url=tool.get('url'), available=tool.get('available')))
        return tools_list

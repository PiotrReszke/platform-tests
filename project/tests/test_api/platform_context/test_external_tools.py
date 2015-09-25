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

from test_utils import ApiTestCase, get_logger
from objects import ExternalTools
import requests
import unittest
from urllib.parse import urlparse

logger = get_logger("test_external_tools")


class TestExternalTools(ApiTestCase):

    # Temporary method for getting response codes from response
    # It could be replaced in the future by adding new property(status code) to return within api_client request method
    # and ignoring that one param in some cases
    def _get_status_code(self, url):
        request = requests.get(url)
        return request.status_code

    def test_check_status_code_of_external_tools(self):
        tools_list = ExternalTools.api_get_external_tools()
        self.assertGreater(len(tools_list), 0)
        for tool in tools_list:
            url_to_check = urlparse(tool.url).scheme + '://' + urlparse(tool.url).hostname
            code_number = self._get_status_code(url_to_check)//100
            if tool.available:
                self.assertInList(code_number, [2, 3])
            else:
                self.assertInList(code_number, [4, 5])

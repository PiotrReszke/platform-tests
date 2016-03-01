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
import unittest

from test_utils import ApiTestCase, priority
from objects import ExternalTools


class ExternalToolsStatus(ApiTestCase):

<<<<<<< HEAD
    @priority.medium
    @unittest.skip("Fix me! DPNG-5105")
=======
    @classmethod
    def setUpClass(cls):
        cls.step("Get list of external tools")
        cls.tools_list = ExternalTools.api_get_external_tools()

<<<<<<< HEAD
>>>>>>> 1958c9c... DPNG-5105 Fix external tools test
=======
    @priority.medium
>>>>>>> f605b47... DPNG-5105 after review
    def test_check_status_code_of_external_tools(self):
        """DPNG-2306 Availability of Arcadia and Hue should be discovered automatically"""
        for tool in self.tools_list:
            if tool.should_have_url:
                with self.subTest(tool=tool.name, available=tool.available):
                    if tool.available and tool.url:
                        self.step("Check that request to {} returns OK status".format(tool.name))
                        tool.send_request()
                    elif tool.url:
                        self.step("Check that request to {} returns fails with 4XX or 5XX".format(tool.name))
                        self.assertReturnsError(tool.send_request)

    @priority.medium
    def test_check_tools_urls(self):
        self.step("Check URL availability of tools")
        for tool in self.tools_list:
            with self.subTest(tool=tool.name, url_present=tool.should_have_url):
                if tool.should_have_url:
                    self.assertIsNotNone(tool.url)
                else:
                    self.assertIsNone(tool.url)

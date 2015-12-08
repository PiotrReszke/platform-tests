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

from test_utils import ApiTestCase, get_logger
from objects import ExternalTools


logger = get_logger("test_external_tools")


class TestExternalTools(ApiTestCase):

    @unittest.expectedFailure
    def test_check_status_code_of_external_tools(self):
        """DPNG-3366 Make Hue available from outside CF network"""
        self.step("Get list of external tools")
        tools_list = ExternalTools.api_get_external_tools()
        self.assertGreater(len(tools_list), 0)
        for tool in tools_list:
            with self.subTest(tool=tool.name):
                if tool.available:
                    self.step("Check that request to {} returns OK status".format(tool.name))
                    tool.send_request()
                else:
                    self.step("Check that request to {} returns fails with 4XX or 5XX".format(tool.name))
                    self.assertReturnsError(tool.send_request)


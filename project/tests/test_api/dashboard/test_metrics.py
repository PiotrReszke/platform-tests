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

from test_utils import ApiTestCase
from test_utils.objects import Organization, ServiceInstance


class MetricsTest(ApiTestCase):

    @classmethod
    def setUpClass(cls):
        cls.seedorg = Organization.get_org_and_space(org_name="seedorg")[0]
        cls.seedorg.api_get_metrics()

    @unittest.expectedFailure
    def test_service_count(self):
        cf_api_service_instances = ServiceInstance.cf_api_get_list_for_org(self.seedorg.guid)
        self.assertEqual(self.seedorg.metrics["service_usage"], len(cf_api_service_instances))

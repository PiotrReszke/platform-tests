#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from test_utils import ApiTestCase
from test_utils.objects import Organization

expected_metrics_keys = ["privateDatasets", "serviceUsagePercent", "datasetCount", "memoryUsageAbsolute", "memoryUsage",
                         "totalUsers", "serviceUsage", "appsRunning", "domainsUsagePercent", "domainsUsage", "appsDown",
                         "publicDatasets"]


class MetricsTest(ApiTestCase):
    @classmethod
    def setUpClass(cls):
        cls.seedorg = Organization.get_org_and_space(org_name="seedorg")[0]
        cls.seedorg.api_get_metrics()

    def test_metrics_contains_all_keys(self):
        keys = list(self.seedorg.metrics.keys())
        self.assertCountEqual(keys, expected_metrics_keys)

    def test_service_count(self):
        apps, services = self.seedorg.cf_api_get_apps_and_services()
        self.assertEqual(self.seedorg.metrics["serviceUsage"], len(services))

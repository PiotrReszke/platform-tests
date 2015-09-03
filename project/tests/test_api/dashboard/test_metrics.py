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
from objects import Organization, DataSet, User


expected_metrics_keys = ["privateDatasets", "serviceUsagePercent", "datasetCount", "memoryUsageAbsolute", "memoryUsage",
                         "totalUsers", "serviceUsage", "appsRunning", "domainsUsagePercent", "domainsUsage", "appsDown",
                         "publicDatasets"]


class MetricsTest(ApiTestCase):
    @classmethod
    def setUpClass(cls):
        cls.seedorg = Organization.get_org_and_space_by_name(org_name="seedorg")[0]
        cls.seedorg.api_get_metrics()

    def test_metrics_contains_all_keys(self):
        keys = list(self.seedorg.metrics.keys())
        self.assertCountEqual(keys, expected_metrics_keys)

    def test_service_count(self):
        apps, services = self.seedorg.cf_api_get_apps_and_services()
        self.assertEqual(self.seedorg.metrics["serviceUsage"], len(services))

    def test_application_metrics(self):
        cl_apps_running = []
        cl_apps_down = []
        org_spaces = self.seedorg.cf_api_get_spaces()
        for space in org_spaces:
            apps, _ = space.cf_api_get_space_summary()
            for app in apps:
                if app.is_started:
                    cl_apps_running.append(app)
                else:
                    cl_apps_down.append(app)
        dashboard_apps_running = self.seedorg.metrics["appsRunning"]
        dashboard_apps_down = self.seedorg.metrics["appsDown"]
        metrics_are_equal = (len(cl_apps_running) == dashboard_apps_running and
                             len(cl_apps_down) == dashboard_apps_down)
        self.assertTrue(metrics_are_equal,
                        "\nApps running: %s - expected: %s\nApps down: %s - expected: %s"
                        % (dashboard_apps_running, len(cl_apps_running), dashboard_apps_down, len(cl_apps_down)))

    def test_user_count(self):
        cl_user_list = User.cf_api_get_list_in_organization(org_guid=self.seedorg.guid)
        dashboard_total_users = self.seedorg.metrics["totalUsers"]
        self.assertTrue(dashboard_total_users == len(cl_user_list),
                        "\nUsers: %s - expected: %s" % (dashboard_total_users, len(cl_user_list)))

    def test_data_metrics(self):
        public_datasets = []
        private_datasets = []
        datasets = DataSet.api_get_list([self.seedorg])
        for set in datasets:
            if set.is_public:
                public_datasets.append(set)
            else:
                private_datasets.append(set)
        dashboard_datasets_count = self.seedorg.metrics['datasetCount']
        dashboard_private_datasets = self.seedorg.metrics['privateDatasets']
        dashboard_public_datasets = self.seedorg.metrics['publicDatasets']
        metrics_are_equal = (len(datasets) == dashboard_datasets_count and
                             len(private_datasets) == dashboard_private_datasets and
                             len(public_datasets) == dashboard_public_datasets)
        self.assertTrue(metrics_are_equal,
                        "\nDatasets count: %s - expected: %s\nPrivate datasets: %s - expected: %s"
                        "\nPublic datasets: %s - expected: %s"
                        % (dashboard_datasets_count, len(datasets), dashboard_private_datasets, len(private_datasets),
                           dashboard_public_datasets, len(public_datasets)))

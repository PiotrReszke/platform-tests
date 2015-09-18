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

import yaml

from test_utils import ApiTestCase, get_logger
from objects import Application, ServiceInstance, ServiceBroker, Organization, github_get_file_content


logger = get_logger("trusted_analytics_app_test")


class TrustedAnalyticsApplicationsSmokeTest(ApiTestCase):
    @classmethod
    def setUpClass(cls):
        settings_file = github_get_file_content(repository="platform-appstack", path="appstack.yml")
        settings = yaml.load(settings_file)
        seedspace_guid = Organization.get_org_and_space_by_name("seedorg", "seedspace")[1].guid
        cls.expected_app_names = {app_info["name"] for app_info in settings["applications"]}
        cls.expected_service_names = {app_info["name"] for app_info in settings["user_provided_service_instances"]}
        cls.expected_broker_names = {app_info["name"] for app_info in settings["service_brokers"]}
        cls.cf_apps = Application.cf_api_get_list(seedspace_guid)
        cls.cf_services = ServiceInstance.cf_api_get_list(seedspace_guid)
        cls.cf_brokers = ServiceBroker.cf_api_get_list(seedspace_guid)
        cls.platform_apps = Application.api_get_list(seedspace_guid)
        cls.platform_services = ServiceInstance.api_get_list(seedspace_guid)

    def test_all_required_apps_are_present_in_cf(self):
        cf_app_names = {a.name for a in self.cf_apps}
        missing_apps = self.expected_app_names - cf_app_names
        self.assertEqual(missing_apps, set(), "Apps missing in cf")

    def test_all_required_apps_are_running_in_cf(self):
        apps_not_running = {a.name for a in self.cf_apps if a.name in self.expected_app_names and not a.is_running}
        self.assertEqual(apps_not_running, set(), "Apps with no running instances in cf")

    def test_all_required_apps_are_present_on_platform(self):
        app_names = {a.name for a in self.platform_apps}
        missing_apps = self.expected_app_names - app_names
        self.assertEqual(missing_apps, set(), "Apps missing on Platform")

    def test_all_required_apps_are_running_on_platform(self):
        apps_not_running = {a.name for a in self.platform_apps if a.name in self.expected_app_names and not a.is_running}
        self.assertEqual(apps_not_running, set(), "Apps with no running instances on Platform")

    def test_apps_have_the_same_details_in_cf_and_on_platform(self):
        only_expected_platform_apps = {app for app in self.platform_apps if app.name in self.expected_app_names}
        for app in only_expected_platform_apps:
            with self.subTest(app=app):
                cf_details = app.cf_api_get_summary()
                platform_details = app.api_get_summary()
                self.assertEqual(cf_details, platform_details, "Different details for {}".format(app.name))

    def test_all_required_service_instances_are_present_in_cf(self):
        cf_service_names = {s.name for s in self.cf_services}
        missing_services = self.expected_service_names - cf_service_names
        self.assertEqual(missing_services, set(), "Services missing in cf")

    def test_all_required_service_instances_are_present_on_platform(self):
        service_names = {s.name for s in self.platform_services}
        missing_services = self.expected_service_names - service_names
        self.assertEqual(missing_services, set(), "Services missing on Platform")

    def test_all_required_brokers_are_present_in_cf(self):
        cf_broker_names = {b.name for b in self.cf_brokers}
        missing_brokers = self.expected_broker_names - cf_broker_names
        self.assertEqual(missing_brokers, set(), "Brokers missing in cf")

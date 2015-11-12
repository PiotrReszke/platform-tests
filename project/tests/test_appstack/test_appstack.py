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

from test_utils import ApiTestCase, get_logger, CONFIG, github_get_file_content
from objects import Application, ServiceInstance, ServiceBroker, Organization


logger = get_logger(__name__)


class TrustedAnalyticsSmokeTest(ApiTestCase):

    @classmethod
    def setUpClass(cls):
        cls.step("Retrieve content of appstack.yml file")
        settings_file = github_get_file_content(repository="platform-appstack", file_path="appstack.yml",
                                                ref=CONFIG["platform_version"])
        settings = yaml.load(settings_file)
        cls.step("Retrieve expected app, service, and broker names from the file")
        cls.expected_app_names = {app_info["name"] for app_info in settings["applications"]}
        cls.expected_upsi_names = {app_info["name"] for app_info in settings["user_provided_service_instances"]}
        cls.expected_broker_names = {app_info["name"] for app_info in settings["service_brokers"]}
        cls.step("Retrieve apps, services, and brokers present in cf")
        ref_space_guid = Organization.get_ref_org_and_space()[1].guid
        cls.cf_apps = Application.cf_api_get_list(ref_space_guid)
        cls.cf_upsi = [s for s in ServiceInstance.cf_api_get_upsi() if s.space_guid == ref_space_guid]
        cls.cf_brokers = ServiceBroker.cf_api_get_list(ref_space_guid)
        cls.step("Retrieve apps and services present on the Platform")
        cls.platform_apps = Application.api_get_list(ref_space_guid)
        cls.platform_instances = ServiceInstance.api_get_list(ref_space_guid)

    def test_all_required_apps_are_present_in_cf(self):
        self.step("Check that all expected apps are present in cf")
        cf_app_names = {a.name for a in self.cf_apps}
        missing_apps = self.expected_app_names - cf_app_names
        self.assertEqual(missing_apps, set(), "Apps missing in cf")

    def test_all_required_apps_are_running_in_cf(self):
        self.step("Check that all expected apps have running instances in cf")
        apps_not_running = {a.name for a in self.cf_apps if a.name in self.expected_app_names and not a.is_running}
        self.assertEqual(apps_not_running, set(), "Apps with no running instances in cf")

    def test_all_required_apps_are_present_on_platform(self):
        self.step("Check that all expected apps are present on the Platform")
        app_names = {a.name for a in self.platform_apps}
        missing_apps = self.expected_app_names - app_names
        self.assertEqual(missing_apps, set(), "Apps missing on the Platform")

    def test_all_required_apps_are_running_on_platform(self):
        self.step("Check that all expected apps have running instances on the Platform")
        apps_not_running = {a.name for a in self.platform_apps if a.name in self.expected_app_names and not a.is_running}
        self.assertEqual(apps_not_running, set(), "Apps with no running instances on the Platform")

    def test_apps_have_the_same_details_in_cf_and_on_platform(self):
        only_expected_platform_apps = {app for app in self.platform_apps if app.name in self.expected_app_names}
        for app in only_expected_platform_apps:
            with self.subTest(app=app.name):
                self.step("Check that details of app {} are the same in cf and on the Platform".format(app.name))
                cf_details = app.cf_api_get_summary()
                platform_details = app.api_get_summary()
                self.assertEqual(cf_details, platform_details, "Different details for {}".format(app.name))

    def test_all_required_service_instances_are_present_in_cf(self):
        self.step("Check that all expected services are present in cf")
        cf_service_names = {s.name for s in self.cf_upsi}
        missing_services = self.expected_upsi_names - cf_service_names
        self.assertEqual(missing_services, set(), "Services missing in cf")

    def test_all_required_service_instances_are_present_on_platform(self):
        self.step("Check that all expected services are present on the Platform")
        service_names = {s.name for s in self.platform_instances}
        missing_services = self.expected_upsi_names - service_names
        self.assertEqual(missing_services, set(), "Services missing on the Platform")

    def test_all_required_brokers_are_present_in_cf(self):
        self.step("Check that all expected service brokers are present in cf")
        cf_broker_names = {b.name for b in self.cf_brokers}
        missing_brokers = self.expected_broker_names - cf_broker_names
        self.assertEqual(missing_brokers, set(), "Brokers missing in cf")



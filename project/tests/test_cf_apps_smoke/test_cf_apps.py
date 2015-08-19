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

import yaml
from urllib.parse import urlparse

from test_utils import ApiTestCase, get_logger
from test_utils.objects import Application, github_get_file_content, ServiceInstance, ServiceBroker, Organization


logger = get_logger("trusted_analytics_app_test")


class TrustedAnalyticsApplicationsSmokeTest(ApiTestCase):
    """A cloned demo-settings.yml is a prerequisite for this test"""

    @classmethod
    def setUpClass(cls):
        # Get expected apps from settings file
        cls.settings_file = github_get_file_content(repository="platform-appstack", path="demo-settings.yml")
        cls.expected_app_and_service_names = []
        cls.expected_service_broker_names = []
        settings = yaml.load(cls.settings_file)
        for app_info in settings["service_brokers"]:
            # We retrieve name and hostname, because some service brokers can use one of them as their name.
            cls.expected_service_broker_names.append((app_info["name"], urlparse(app_info["broker_url"])
                                                      .hostname.split(".")[0]))
        # helper list for preventing names duplication
        tmp_list = [name for pair in cls.expected_service_broker_names for name in pair]
        for app_info in settings["applications"] + settings["user_provided_service_instances"]:
            name = app_info["name"]
            if "credentials" in app_info and "host" in app_info["credentials"]:
                name = urlparse(app_info["credentials"]["host"]).hostname.split(".")[0]
            if name not in tmp_list:
                cls.expected_app_and_service_names.append(name)
        logger.info("{} apps/services/brokers are expected to be started"
                    .format(len(cls.expected_app_and_service_names) + len(cls.expected_service_broker_names)))
        cls.seedspace_guid = Organization.get_org_and_space("seedorg", "seedspace")[1].guid

    def test_cf_application_status(self):
        """Check that all applications from demo-settings.yml are started on cf"""
        cf_apps = Application.cf_api_get_list(self.seedspace_guid)
        cf_services = ServiceInstance.cf_api_get_list(self.seedspace_guid)
        cf_service_brokers = ServiceBroker.cf_api_get_list(self.seedspace_guid)
        app_names = set([app.name for app in cf_apps + cf_services + cf_service_brokers])
        logger.info("There are %s apps/services/brokers on cf", len(app_names))
        # find out which apps are missing
        missing_apps = [name for name in self.expected_app_and_service_names if name not in app_names]
        missing_apps = missing_apps + [name for name, hostname in self.expected_service_broker_names
                                       if not (name in app_names or hostname in app_names)]
        # create list of apps/services/brokers that are running
        running_apps = [name for name in app_names
                        if name not in missing_apps and name in self.expected_app_and_service_names]
        running_apps = running_apps + [name for name, hostname in self.expected_service_broker_names
                                       if not (name in missing_apps and hostname in missing_apps)]
        logger.info("\nRunning apps/services/brokers: %s\n", running_apps)
        # check that all expected apps are running
        apps_not_started = [app.name for app in cf_apps
                            if app.name in self.expected_app_and_service_names and not app.is_started]
        # assert that both conditions are satisfied
        self.assertTrue((missing_apps == [] and apps_not_started == []),
                        "\nMissing applications: {}\nApplications not started: {}"
                        .format(missing_apps, apps_not_started))

    def test_trusted_analytics_apps(self):
        """Verify applications on platform against demo-settings.yml"""
        platform_app_list = Application.api_get_list(self.seedspace_guid)
        services_app_list = ServiceInstance.api_get_list(self.seedspace_guid)
        logger.info("There are {} apps/services on the platform".format(len(platform_app_list + services_app_list)))
        platform_app_and_service_names = [app.name for app in platform_app_list + services_app_list]
        missing_apps = [name for name in self.expected_app_and_service_names
                        if name not in platform_app_and_service_names + services_app_list]
        self.assertTrue(missing_apps == [], "Apps missing in platform: {}".format(missing_apps))

    def test_trusted_analytics_applications_details(self):
        """Verify application details between CF API and Platform API"""
        platform_api_apps = Application.api_get_list(self.seedspace_guid)
        expected_platform_apps = [app for app in platform_api_apps if app.name in self.expected_app_and_service_names]
        different_apps = []
        for app in expected_platform_apps:
            logger.info("Comparing details of {}".format(app.name))
            cf_details = app.cf_api_get_summary()  # get app details from CF api
            console_details = app.api_get_summary()  # get app details from console
            differences = [key for key, val in cf_details.items() if console_details[key] != val]
            if differences:
                different_apps.append(app.name)
                logger.warning("Details of app '{}' differ: {}".format(app.name, differences))
        self.assertTrue(different_apps == [], "There are differences in app details for {}".format(different_apps))

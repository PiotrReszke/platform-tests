from test_utils import ApiTestCase, get_logger, config
from test_utils.objects import Application, github_get_file_content, Organization


logger = get_logger("trusted_analytics_app_test")


class TrustedAnalyticsApplicationsSmokeTest(ApiTestCase):
    """A cloned demo-settings.yml is a prerequisite for this test"""

    @classmethod
    def setUpClass(cls):
        cls.settings_file = github_get_file_content(repository="platform-appstack", path="demo-settings.yml")
        # Get expected apps from settings file
        cls.expected_apps = Application.get_list_from_settings_yml(cls.settings_file)
        cls.expected_app_names = [app.name for app in cls.expected_apps]
        logger.info("{} apps are expected to be started".format(len(cls.expected_apps)))
        cls.seedspace_guid = Organization.get_org_and_space("seedorg", "seedspace")[1].guid

    def test_cf_application_status(self):
        """Check that all applications from demo-settings.yml are started on cf"""
        cf_apps = Application.cf_api_get_list(self.seedspace_guid)
        logger.info("There are {} apps on cf".format(len(cf_apps)))
        # find out which apps are missing
        app_names = [app.name for app in cf_apps]
        missing_apps = [name for name in self.expected_app_names if name not in app_names]
        # check that all expected apps are running
        apps_not_started = [app.name for app in cf_apps if app.name in self.expected_app_names and not app.is_started]
        # assert that both conditions are satisfied
        self.assertTrue((missing_apps == [] and apps_not_started == []),
                        "\nMissing applications: {}\nApplications not started: {}".format(missing_apps,
                                                                                          apps_not_started))

    def test_trusted_analytics_apps(self):
        """Verify applications on platform against demo-settings.yml"""
        platform_app_list = Application.api_get_list(self.seedspace_guid)
        logger.info("There are {} apps on the platform".format(len(platform_app_list)))
        platform_app_names = [app.name for app in platform_app_list]
        missing_apps = [name for name in self.expected_app_names if name not in platform_app_names]
        self.assertTrue(missing_apps == [], "Apps missing in platform: {}".format(missing_apps))

    def test_trusted_analytics_applications_details(self):
        """Verify application details between CF API and Platform API"""
        platform_api_apps = Application.api_get_list(self.seedspace_guid)
        expected_platform_apps = [app for app in platform_api_apps if app.name in self.expected_app_names]
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

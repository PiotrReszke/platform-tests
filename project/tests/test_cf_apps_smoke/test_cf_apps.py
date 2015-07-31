from test_utils import ApiTestCase, get_logger, config, cf_login
from test_utils.objects import Application, github_get_file_content
from test_utils.api_client import UnexpectedResponseError


logger = get_logger("trusted_analytics_app_test")


class TrustedAnalyticsApplicationsSmokeTest(ApiTestCase):
    """A cloned demo-settings.yml is a prerequisite for this test"""

    @classmethod
    def setUpClass(cls):
        cls.settings_file = github_get_file_content(repository="platform-appstack", path="demo-settings.yml")
        cf_login("seedorg", "seedspace")
        cls.seedspace_guid = config.get_config_value("seedspace_guid")

    def test_cf_application_status(self):
        """Check that all applications from demo-settings.yml are started on cf"""
        expected_apps = Application.get_list_from_settings(self.settings_file)
        logger.info("{} apps are expected to be started".format(len(expected_apps)))
        apps = Application.cf_api_get_list(self.seedspace_guid)
        logger.info("There are {} apps on cf".format(len(apps)))
        # find out which apps are missing
        expected_app_names = [app.name for app in expected_apps]
        app_names = [app.name for app in apps]
        missing_apps = [name for name in expected_app_names if name not in app_names]
        # check that all expected apps are running
        apps_not_started = [app.name for app in apps if app.name in expected_app_names and not app.is_started]
        # assert that both conditions are satisfied
        self.assertTrue((missing_apps == [] and apps_not_started == []),
                        "\nMissing applications: {}\nApplications not started: {}".format(missing_apps, apps_not_started))

    def test_trusted_analytics_applications_details(self):
        """Verify application details between cf and Platform API"""
        # Get expected apps from settings file
        expected_apps = Application.get_list_from_settings(self.settings_file)
        # Get apps list from console
        apps_list = Application.api_get_apps_list(self.seedspace_guid)
        missing_apps = []
        different_apps = []
        for app in expected_apps:
            try:
                app_guid = (next(x for x in apps_list if x.name == app.name)).guid
                # Get app details from CLI
                cli_app = Application.cf_get_app_summary(app_guid)
                # Get app details from console
                console_app = Application.api_get_app_summary(app_guid)
                if 'error_code' not in cli_app:
                    logger.info("Comparing details of %s app", app.name)
                    different_details = Application.compare_details(cli_app, console_app)
                    if len(different_details) > 0:
                        different_apps.append(app.name)
                        logger.warning("Application '%s' has different details: %s",
                                       app.name, ', '.join(different_details))
                else:
                    missing_apps.append(app.name)
            except (StopIteration, UnexpectedResponseError):
                missing_apps.append(app.name)
        self.assertTrue((missing_apps == [] and different_apps == []),
                        "\nExpected applications: {}\nMissing applications({}): {}\nApplications with different env details({}): {}"
                        .format(len(expected_apps), len(missing_apps), ", ".join(missing_apps), len(different_apps),
                                ", ".join(different_apps)))





from test_utils import ApiTestCase, get_logger
from test_utils import cf_login, CfApplication, github_get_file_content


logger = get_logger("cf_app_test")


class CloudFoundryApplications(ApiTestCase):

    @classmethod
    def setUpClass(cls):
        cls.settings_file = github_get_file_content(repository="platform-appstack", path="demo-settings.yml")
        cf_login("seedorg", "seedspace")

    def test_cf_application_status(self):
        """A cloned demo-settings.yml is a prerequisite for this test"""
        expected_apps = CfApplication.get_list_from_settings(self.settings_file)
        logger.info("{} apps are expected to be started".format(len(expected_apps)))
        apps = CfApplication.cf_get_list()
        logger.info("There are {} apps on cf".format(len(apps)))
        # find out which apps are missing
        expected_app_names = [app.name for app in expected_apps]
        app_names = [app.name for app in apps]
        missing_apps = [name for name in expected_app_names if name not in app_names]
        # check that all expected apps are running
        apps_not_started = [app.name for app in apps if app.name in expected_app_names and app.state != "started"]
        # assert that both conditions are satisfied
        self.assertTrue((missing_apps == [] and apps_not_started == []),
                        "\nMissing applications: {}\nApplications not started: {}".format(missing_apps, apps_not_started))





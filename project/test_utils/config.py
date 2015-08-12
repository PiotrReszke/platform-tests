import argparse
import configparser
import os


__all__ = ["APP_SCHEMAS", "TEST_SETTINGS", "update_test_settings", "parse_arguments", "get_config_value",
           "get_ssh_key_passphrase"]


# configuration variables depending on the environment
CONFIG = {
    "gotapaas.eu": {
        "api_endpoint": "gotapaas.eu",
        "login.do_scheme": "https",
        "login_endpoint": "login.gotapaas.eu",
        "cf_endpoint": "api.gotapaas.eu",
        "admin_guid": "c2c34a64-2869-4947-bd35-b2bed9f49dfe",
        "admin_username": "trusted.analytics.tester@gmail.com",
        "seedorg_guid": "ee1c60ab-1d4f-4bbb-aeba-60ea8c67ba9b",
        "seedspace_guid": "fceadf34-f597-4634-8dd2-1875c06b9c9c",
        "cdh_host": "cdh.gotapaas.eu",
        "uaa": "uaa.gotapaas.eu"
    },
    "demo-gotapaas.com": {
        "api_endpoint": "demo-gotapaas.com",
        "login.do_scheme": "http",
        "login_endpoint": "login.demo-gotapaas.com",
        "cf_endpoint": "api.demo-gotapaas.com",
        "admin_guid": "284b34e8-6c23-4d64-afd1-952a394df501",
        "admin_username": "trusted.analytics.tester@gmail.com",
        "seedorg_guid": "79d9c4ec-292c-48b4-9d7e-87ff62f86b1e",
        "seedspace_guid": "2b92e961-0ff8-4fe1-8a14-b8b491b05700",
        "cdh_host": "cdh.demo-gotapaas.com",
        "uaa": "login.demo-gotapaas.com"
    }
}


# schema paths for each application
APP_SCHEMAS = {
    "das": "swagger/data_acquisition_service_swagger.json",
    "data-catalog": "swagger/data_catalog_swagger.json",
    "latest-events-service": "swagger/latest_events_service_swagger.json",
    "metrics-provider": "swagger/metrics_provider_swagger.json",
    "user-management": "swagger/user_management_swagger.json",
    "service-catalog": "swagger/service_catalog_swagger.json",
    "app-launcher-helper": "swagger/app_launcher_helper_swagger.json",
    "hive": "swagger/hive_swagger.json"
}


# passwords and other secrets
__SECRET = configparser.ConfigParser()
__SECRET.read("test_utils/secrets/.secret.ini")


TEST_SETTINGS = {
    "GITHUB_AUTH": (__SECRET["github"]["username"], __SECRET["github"]["password"]),
    "TEST_EMAIL": "intel.data.tests@gmail.com"
}


def update_test_settings(client_type=None, test_environment=None, test_username=None, proxy=None):
    TEST_SETTINGS["TEST_ENVIRONMENT"] = test_environment or TEST_SETTINGS["TEST_ENVIRONMENT"]
    TEST_SETTINGS["TEST_USERNAME"] = test_username or TEST_SETTINGS["TEST_USERNAME"]
    TEST_SETTINGS["TEST_PROXY"] = proxy
    TEST_SETTINGS["TEST_CLIENT_TYPE"] = client_type or TEST_SETTINGS["TEST_CLIENT_TYPE"]
    TEST_SETTINGS["TEST_PASSWORD"] = __SECRET[TEST_SETTINGS["TEST_ENVIRONMENT"]][TEST_SETTINGS["TEST_USERNAME"]]
    TEST_SETTINGS["TEST_LOGIN_TOKEN"] = __SECRET[TEST_SETTINGS["TEST_ENVIRONMENT"]]["login_token"]


def parse_arguments():
    parser = argparse.ArgumentParser(description="Platform API Automated Tests")
    parser.add_argument("-e",
                        "--environment",
                        default=None,
                        help="environment where tests are to be run, e.g. gotapaas.eu")
    parser.add_argument("-u",
                        "--username",
                        default=None,
                        help="username for logging into Cloud Foundry")
    parser.add_argument("--proxy",
                        default=None,
                        help="set proxy for api client")
    parser.add_argument("--test",
                        default=None,
                        help="choose a group of tests which should be executed")
    parser.add_argument("--client-type",
                        default="console",
                        choices=["console", "app"],
                        help="choose a client type for tests")
    return parser.parse_args()


def get_config_value(key):
    """Return config value for current environment"""
    test_environment = TEST_SETTINGS["TEST_ENVIRONMENT"]
    return CONFIG[test_environment][key]

def get_ssh_key_passphrase():
    if __SECRET.has_section("ssh"):
        return __SECRET["ssh"]["passphrase"]

def get_github_username():
    return __SECRET["github"]["username"]

def get_github_password():
    return __SECRET["github"]["password"]


# default settings
update_test_settings(client_type="console",
                     test_environment="gotapaas.eu",
                     test_username="trusted.analytics.tester@gmail.com",
                     proxy="proxy-mu.intel.com:911")
# change settings when tests are run with PyCharm runner using environment variables
update_test_settings(client_type=os.environ.get("TEST_CLIENT_TYPE"),
                     test_environment=os.environ.get("TEST_ENVIRONMENT"),
                     test_username=os.environ.get("TEST_USERNAME"),
                     proxy=os.environ.get("TEST_PROXY"))


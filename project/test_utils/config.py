import argparse
import configparser
import os
import sys

__all__ = ["APP_SCHEMAS", "TEST_SETTINGS", "CONFIG"]

# configuration variables depending on the environment
CONFIG = {
    "gotapaas.eu": {
        "api_endpoint": "apps.gotapaas.eu",
        "login_endpoint": "login.run.gotapaas.eu",
        "admin_guid": "13c32424-23f4-44f7-bbb9-60763bfab4bc"
    },
    "demo-gotapaas.com": {
        "api_endpoint": "demo-gotapaas.com",
        "login_endpoint": "login.demo-gotapaas.com",
        "admin_guid": ""
    }
}

# schema paths for each application
APP_SCHEMAS = {
    "user-management": "swagger/user_management_swagger.json",
    "data-catalog": "swagger/data_catalog_swagger.json",
    "das": "swagger/data_acquisition_service_swagger.json"
}

# passwords and other secrets
__SECRET = configparser.ConfigParser()
__SECRET.read("test_utils/.secret.ini")


def update_test_settings(test_environment=None, test_username=None, proxy=None, password=None, login_token=None):
    TEST_SETTINGS["TEST_ENVIRONMENT"] = test_environment or TEST_SETTINGS["TEST_ENVIRONMENT"]
    TEST_SETTINGS["TEST_USERNAME"] = test_username or TEST_SETTINGS["TEST_USERNAME"]
    TEST_SETTINGS["TEST_PROXY"] = proxy
    secret_password = secret_login_token = None
    if __SECRET.has_section(TEST_SETTINGS["TEST_ENVIRONMENT"]):
        secret_password = __SECRET[TEST_SETTINGS["TEST_ENVIRONMENT"]][TEST_SETTINGS["TEST_USERNAME"]]
        secret_login_token = __SECRET[TEST_SETTINGS["TEST_ENVIRONMENT"]]["login_token"]
    TEST_SETTINGS["TEST_PASSWORD"] = password or secret_password
    TEST_SETTINGS["TEST_LOGIN_TOKEN"] = login_token or secret_login_token


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
    parser.add_argument("-p",
                        "--password",
                        default=None,
                        help="password matching environment and username")
    parser.add_argument("-l",
                        "--login-token",
                        default=None,
                        help="authorization token for cf login")
    parser.add_argument("--proxy",
                        default=None,
                        help="set proxy for api client")
    parser.add_argument("--test",
                        default=None,
                        help="choose a group of tests which should be executed")
    return parser.parse_args()


TEST_SETTINGS = {}
# default settings
update_test_settings(test_environment="gotapaas.eu", test_username="admin", proxy="proxy-mu.intel.com:911")
# change settings when tests are run with PyCharm runner using environment variables
update_test_settings(test_environment=os.environ.get("TEST_ENVIRONMENT"),
                       test_username=os.environ.get("TEST_USERNAME"),
                       proxy=(os.environ.get("TEST_PROXY") or TEST_SETTINGS["TEST_PROXY"]),
                       password=os.environ.get("TEST_PASSWORD"),
                       login_token=os.environ.get("TEST_LOGIN_TOKEN"))







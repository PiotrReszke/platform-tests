import argparse
import configparser
import os


__all__ = ["APP_SCHEMAS", "TEST_SETTINGS", "update_test_settings", "parse_arguments", "get_config_value",
           "get_ssh_key_passphrase"]


# configuration variables depending on the environment
CONFIG = {
    "gotapaas.eu": {
        "api_endpoint": "apps.gotapaas.eu",
        "login.do_scheme": "https",
        "login_endpoint": "login.run.gotapaas.eu",
        "cf_endpoint": "api.run.gotapaas.eu",
        "admin_guid": "13c32424-23f4-44f7-bbb9-60763bfab4bc",
        "admin_username": "admin",
        "seedorg_guid": "69e8563a-f182-4c1a-9b9d-9a475297cb41",
        "seedspace_guid": "16829796-2b3a-4c98-ad08-166315ca1411",
        "cdh_host": "cdh.gotapaas.eu"
    },
    "demo-gotapaas.com": {
        "api_endpoint": "demo-gotapaas.com",
        "login.do_scheme": "http",
        "login_endpoint": "login.demo-gotapaas.com",
        "cf_endpoint": "api.demo-gotapaas.com",
        "admin_guid": "284b34e8-6c23-4d64-afd1-952a394df501",
        "admin_username": "tester-admin",
        "seedorg_guid": "79d9c4ec-292c-48b4-9d7e-87ff62f86b1e",
        "seedspace_guid": "2b92e961-0ff8-4fe1-8a14-b8b491b05700",
        "cdh_host": "cdh.demo-gotapaas.com"
    }
}


# schema paths for each application
APP_SCHEMAS = {
    "das": "swagger/data_acquisition_service_swagger.json",
    "data-catalog": "swagger/data_catalog_swagger.json",
    "metrics-provider": "swagger/metrics_provider_swagger.json",
    "service-catalog": "swagger/service_catalog_swagger.json",
    "user-management": "swagger/user_management_swagger.json"
}


# passwords and other secrets
__SECRET = configparser.ConfigParser()
__SECRET.read("test_utils/secrets/.secret.ini")


TEST_SETTINGS = {}


def update_test_settings(client_type, test_environment=None, test_username=None, proxy=None, password=None, login_token=None,
                         github_auth=(), test_email=None):
    TEST_SETTINGS["TEST_ENVIRONMENT"] = test_environment or TEST_SETTINGS["TEST_ENVIRONMENT"]
    TEST_SETTINGS["TEST_USERNAME"] = test_username or TEST_SETTINGS["TEST_USERNAME"]
    TEST_SETTINGS["TEST_PROXY"] = proxy
    secret_password = secret_login_token = None
    if __SECRET.has_section(TEST_SETTINGS["TEST_ENVIRONMENT"]):
        secret_password = __SECRET[TEST_SETTINGS["TEST_ENVIRONMENT"]][TEST_SETTINGS["TEST_USERNAME"]]
        secret_login_token = __SECRET[TEST_SETTINGS["TEST_ENVIRONMENT"]]["login_token"]
    TEST_SETTINGS["TEST_PASSWORD"] = password or secret_password
    TEST_SETTINGS["TEST_LOGIN_TOKEN"] = login_token or secret_login_token
    TEST_SETTINGS["GITHUB_AUTH"] = github_auth or TEST_SETTINGS.get("GITHUB_AUTH")
    TEST_SETTINGS["TEST_EMAIL"] = test_email or TEST_SETTINGS["TEST_EMAIL"]
    TEST_SETTINGS["TEST_CLIENT_TYPE"] = client_type


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
    parser.add_argument("--github-username",
                        default=None,
                        help="username in GitHub")
    parser.add_argument("--github-password",
                        default=None,
                        help="password matching GitHub username")
    parser.add_argument("--client-type",
                        default="console",
                        help="choose a client type for tests")
    return parser.parse_args()


def get_config_value(key):
    """Return config value for current environment"""
    test_environment = TEST_SETTINGS["TEST_ENVIRONMENT"]
    return CONFIG[test_environment][key]

def get_ssh_key_passphrase():
    if __SECRET.has_section("ssh"):
        return __SECRET["ssh"]["passphrase"]

# default settings
__github_auth = None
if __SECRET.has_section("github"):
    __github_auth = (__SECRET["github"]["username"], __SECRET["github"]["password"])
update_test_settings(client_type="console",
                     test_environment="gotapaas.eu",
                     test_username="admin",
                     proxy="proxy-mu.intel.com:911",
                     github_auth=__github_auth,
                     test_email="intel.data.tests@gmail.com")
# change settings when tests are run with PyCharm runner using environment variables
update_test_settings(client_type="console",
                     test_environment=os.environ.get("TEST_ENVIRONMENT"),
                     test_username=os.environ.get("TEST_USERNAME"),
                     proxy=(os.environ.get("TEST_PROXY") or TEST_SETTINGS["TEST_PROXY"]),
                     password=os.environ.get("TEST_PASSWORD"),
                     login_token=os.environ.get("TEST_LOGIN_TOKEN"),
                     github_auth=__github_auth)


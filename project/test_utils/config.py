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

import argparse
import configparser
import os


__all__ = ["TEST_SETTINGS", "update_test_settings", "parse_arguments", "get_config_value",
           "get_ssh_key_passphrase", "get_password"]


# configuration variables depending on the environment
CONFIG = {
    "gotapaas.eu": {
        "api_endpoint": "gotapaas.eu",
        "login.do_scheme": "https",
        "login_endpoint": "login.gotapaas.eu",
        "cf_endpoint": "api.gotapaas.eu",
        "admin_username": "trusted.analytics.tester@gmail.com",
        "cdh_host": "cdh.gotapaas.eu",
        "uaa": "uaa.gotapaas.eu"
    },
    "demo-gotapaas.com": {
        "api_endpoint": "demo-gotapaas.com",
        "login.do_scheme": "http",
        "login_endpoint": "login.demo-gotapaas.com",
        "cf_endpoint": "api.demo-gotapaas.com",
        "admin_username": "trusted.analytics.tester@gmail.com",
        "cdh_host": "cdh.demo-gotapaas.com",
        "uaa": "login.demo-gotapaas.com"
    },
    "callisto.gotapaas.com": {
        "api_endpoint": "callisto.gotapaas.com",
        "login.do_scheme": "http",
        "login_endpoint": "login.callisto.gotapaas.com",
        "cf_endpoint": "api.callisto.gotapaas.com",
        "admin_username": "trusted.analytics.tester@gmail.com",
        "cdh_host": "cdh.callisto.gotapaas.com",
        "uaa": "login.callisto.gotapaas.com"
    },
    "daily.gotapaas.com": {
        "api_endpoint": "daily.gotapaas.com",
        "login.do_scheme": "http",
        "login_endpoint": "login.daily.gotapaas.com",
        "cf_endpoint": "api.daily.gotapaas.com",
        "admin_username": "trusted.analytics.tester@gmail.com",
        "cdh_host": "cdh.daily.gotapaas.com",
        "uaa": "login.daily.gotapaas.com"
    },
    "sprint.gotapaas.com": {
        "api_endpoint": "sprint.gotapaas.com",
        "login.do_scheme": "http",
        "login_endpoint": "login.sprint.gotapaas.com",
        "cf_endpoint": "api.sprint.gotapaas.com",
        "admin_username": "trusted.analytics.tester@gmail.com",
        "cdh_host": "cdh.sprint.gotapaas.com",
        "uaa": "login.sprint.gotapaas.com"
    },
    "10.91.120.35.xip.io": {
        "api_endpoint": "10.91.120.35.xip.io",
        "login.do_scheme": "http",
        "login_endpoint": "login.10.91.120.35.xip.io",
        "cf_endpoint": "api.10.91.120.35.xip.io",
        "admin_username": "jacek.skowron@intel.com",
        "cdh_host": "cdh.10.91.120.35.xip.io",
        "uaa": "login.10.91.120.35.xip.io"
    }
}


# passwords and other secrets
__SECRET = configparser.ConfigParser()
__SECRET.read("test_utils/secrets/.secret.ini")


TEST_SETTINGS = {
    "GITHUB_AUTH": (__SECRET["github"]["username"], __SECRET["github"]["password"]),
    "TEST_EMAIL": "intel.data.tests@gmail.com",
    "TEST_DISABLE_SSL_VALIDATION": False
}


def update_test_settings(client_type=None, test_environment=None, test_username=None, proxy=None,
                         disable_ssl_validation=None):
    TEST_SETTINGS["TEST_ENVIRONMENT"] = test_environment or TEST_SETTINGS["TEST_ENVIRONMENT"]
    TEST_SETTINGS["TEST_USERNAME"] = test_username or TEST_SETTINGS["TEST_USERNAME"]
    TEST_SETTINGS["TEST_PROXY"] = proxy
    TEST_SETTINGS["TEST_DISABLE_SSL_VALIDATION"] = (disable_ssl_validation or
                                                    TEST_SETTINGS["TEST_DISABLE_SSL_VALIDATION"])
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
    parser.add_argument("--disable-ssl-validation",
                        action="store_true",
                        help="Disable SSL validation")
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


def get_password(username):
    return __SECRET[TEST_SETTINGS["TEST_ENVIRONMENT"]][username]


# default settings
update_test_settings(client_type="console",
                     test_environment="gotapaas.eu",
                     test_username="trusted.analytics.tester@gmail.com",
                     proxy="proxy-mu.intel.com:911",
                     disable_ssl_validation=False)
# change settings when tests are run with PyCharm runner using environment variables
update_test_settings(client_type=os.environ.get("TEST_CLIENT_TYPE"),
                     test_environment=os.environ.get("TEST_ENVIRONMENT"),
                     test_username=os.environ.get("TEST_USERNAME"),
                     proxy=os.environ.get("TEST_PROXY"),
                     disable_ssl_validation=(os.environ.get("TEST_DISABLE_SSL_VALIDATION") == 'True'))


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
from datetime import datetime
import os
import re
import socket

from . import logger


__all__ = ["update_test_config", "parse_arguments", "CONFIG", "is_test_object_name", "get_test_name"]


def is_test_object_name(name):
    """Return True if object's name matches pattern for test names, False otherwise."""
    if name is None:
        return False  # there are users with username=None
    test_name_regex = "^.+[0-9]{8}_[0-9]{6}_{0,1}[0-9]{0,6}(@gmail.com){0,1}$"
    return re.match(test_name_regex, name) is not None


def get_test_name(email=False, short=False):
    """Return string with hostname and date for use as name of test org, user, transfer, etc."""
    str_format = "%Y%m%d_%H%M%S" if short else "%Y%m%d_%H%M%S_%f"
    hostname = socket.gethostname().replace("-", "_").lower()
    now = datetime.now().strftime(str_format)
    name_format = CONFIG["test_user_email"].replace('@', '+{}_{}@') if email else "{}_{}"
    return name_format.format(hostname, now)


# secrets config
__SECRETS = configparser.ConfigParser()
__SECRETS.read(os.path.join("test_utils", "secrets", ".secret.ini"))
# configuration variables depending on the environment
__CONFIG = configparser.ConfigParser()
__CONFIG.read_string("""
    [DEFAULT]
        admin_username = trusted.analytics.tester@gmail.com
        login.do_scheme = http
        ssl_validation = False
        ref_org_name = seedorg
        ref_space_name = seedspace
        cdh_key_path = ~/.ssh/auto-deploy-virginia.pem
    [gotapaas.eu]
        login.do_scheme = https
        ssl_validation = True
    [demo-gotapaas.com]
        ssl_validation = True
        cdh_key_path = ~/.ssh/demo-gotapaas.pem
""")


# current test settings - set values constant for all environments
CONFIG = {
    "github_auth": (__SECRETS["github"]["username"], __SECRETS["github"]["password"]),
    "ssh_key_passphrase": __SECRETS["ssh"].get("passphrase", ""),
    "test_user_email": "intel.data.tests@gmail.com"
}


def update_test_config(domain=None, proxy=None, client_type=None, logged_response_body_length=None,
                       logging_level=None, platform_version="master"):
    defaults = __CONFIG.defaults()
    defaults.update(__SECRETS.defaults())
    CONFIG["platform_version"] = platform_version
    if domain is not None:
        CONFIG["domain"] = domain
        CONFIG["admin_username"] = __CONFIG.get(domain, "admin_username", fallback=defaults["admin_username"])
        CONFIG["admin_password"] = __SECRETS.get(domain, CONFIG["admin_username"],
                                                 fallback=defaults[CONFIG["admin_username"]])
        CONFIG["login_token"] = __SECRETS.get(domain, "login_token", fallback=defaults["login_token"])
        CONFIG["uaa_token"] = __SECRETS.get(domain, "uaa_token", fallback=defaults["uaa_token"])
        CONFIG["uaa_admin_token"] = __SECRETS.get(domain, "uaa_admin_token", fallback=defaults["uaa_admin_token"])
        CONFIG["login.do_scheme"] = __CONFIG.get(domain, "login.do_scheme", fallback=defaults["login.do_scheme"])
        CONFIG["ssl_validation"] = __CONFIG.getboolean(domain, "ssl_validation",
                                                       fallback=__CONFIG.getboolean("DEFAULT", "ssl_validation"))
        CONFIG["ref_org_name"] = __CONFIG.get(domain, "ref_org_name", fallback=defaults["ref_org_name"])
        CONFIG["ref_space_name"] = __CONFIG.get(domain, "ref_space_name", fallback=defaults["ref_space_name"])
        CONFIG["cdh_key_path"] = __CONFIG.get(domain, "cdh_key_path", fallback=defaults["cdh_key_path"])
    CONFIG["proxy"] = proxy
    if logged_response_body_length is not None:
        logger.LOGGED_RESPONSE_BODY_LENGTH = logged_response_body_length
    if client_type is not None:
        CONFIG["client_type"] = client_type
    if logging_level is not None:
        logger.set_level(logging_level)


# update settings using default values
update_test_config(domain="daily.gotapaas.com",
                   proxy="proxy-mu.intel.com:911",
                   client_type="console",
                   logged_response_body_length=1024,
                   logging_level="DEBUG")
# update settings using environment variables (when tests are run with PyCharm runner)
update_test_config(domain=os.environ.get("TEST_ENVIRONMENT"),
                   proxy=os.environ.get("TEST_PROXY"),
                   client_type=os.environ.get("TEST_CLIENT_TYPE"),
                   logged_response_body_length=os.environ.get("LOGGED_RESPONSE_BODY_LENGTH"),
                   platform_version=os.environ.get("PLATFORM_VERSION", "master"))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Platform API Automated Tests")
    parser.add_argument("-e", "--environment",
                        help="environment where tests are to be run, e.g. gotapaas.eu",
                        required=True)
    parser.add_argument("-s", "--suite",
                        default=None,
                        help="a group of tests to execute (directory or file path)")
    parser.add_argument("-t", "--test",
                        default=None,
                        help="pass single test name")
    parser.add_argument("-v", "--platform-version",
                        default="master",
                        help="Platform version tag name")
    parser.add_argument("--proxy",
                        default=None,
                        help="set proxy for api client")
    parser.add_argument("--client-type",
                        default="console",
                        choices=["console", "app"],
                        help="choose a client type for tests")
    parser.add_argument("--logged-response-body-length",
                        default=1024,
                        help="Limit response body length that is logged. Set to -1 to log full body.")
    parser.add_argument("-l", "--logging-level",
                        choices=["DEBUG", "INFO", "WARNING"],
                        default="DEBUG")
    parser.add_argument("-d", "--log-file-directory",
                        default="/tmp",
                        help="Change default log file directory.")
    return parser.parse_args()

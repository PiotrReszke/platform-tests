#
# Copyright (c) 2016 Intel Corporation
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

from modules import tap_logger
from modules.markers import priority


# secrets config
secret_file_path = os.path.join("configuration", "secrets", ".secret.ini")
__SECRETS = configparser.ConfigParser()
__SECRETS.read(secret_file_path)
# configuration variables depending on the environment
__CONFIG = configparser.ConfigParser()
__CONFIG.read_string("""
    [DEFAULT]
        admin_username = trusted.analytics.tester@gmail.com
        login.do_scheme = http
        ssl_validation = False
        cf_api_version = v2
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
    "github_auth": (__SECRETS.get("github", "username", fallback=""),
                    __SECRETS.get("github", "password", fallback="")),
    "ssh_key_passphrase": __SECRETS.get("ssh", "passphrase", fallback=""),
    "test_user_email": "intel.data.tests@gmail.com",
    "database_url": None,
    "failed_tests_file_path": os.path.join("..", "failed_tests.log"),
    "remote_log_enabled": True,
    "remote_logger_retry_count": 5,
    "cf_auth": ("cf", ""),
    "kerberos": False,
    "pushed_app_proxy": None,
}

LOGGED_CONFIG_KEYS = ["domain", "admin_username", "client_type", "ssl_validation", "platfom_version", "database_url",
                      "ref_org_name", "ref_space_name", "jumpbox_address", "elasticsearch_host"]


def update_test_config(domain=None, client_type=None, logged_response_body_length=None,
                       logging_level=None, repository=None, platform_version="master", database_url=None,
                       test_suite=None, local_appstack=None, admin_username=None, admin_password=None,
                       ref_org_name=None, ref_space_name=None, test_run_id=None, disable_remote_logger=None,
                       remote_logger_retry_count=None, kerberos=None, jumpbox_address=None, kubernetes=None,
                       pushed_app_proxy=None, elasticsearch_host=None):
    defaults = __CONFIG.defaults()
    defaults.update(__SECRETS.defaults())
    CONFIG["platform_version"] = platform_version

    if domain is not None:
        CONFIG["domain"] = domain

        setup_admin_login(domain, defaults, admin_username, admin_password)

        CONFIG["uaa_token"] = __SECRETS.get(domain, "uaa_token", fallback=defaults.get("uaa_token", None))
        CONFIG["login.do_scheme"] = __CONFIG.get(domain, "login.do_scheme",
                                                 fallback=defaults.get("login.do_scheme", None))
        CONFIG["ssl_validation"] = __CONFIG.getboolean(domain, "ssl_validation",
                                                       fallback=__CONFIG.getboolean("DEFAULT", "ssl_validation"))
        CONFIG["cdh_key_path"] = __CONFIG.get(domain, "cdh_key_path", fallback=defaults.get("cdh_key_path", None))
        CONFIG["arcadia_username"] = __SECRETS.get(domain, "arcadia_username",
                                                   fallback=defaults.get("arcadia_username", None))
        CONFIG["arcadia_password"] = __SECRETS.get(domain, "arcadia_password",
                                                   fallback=defaults.get("arcadia_password", None))
        CONFIG["cloudera_username"] = __SECRETS.get(domain, "cloudera_username",
                                                    fallback=defaults.get("cloudera_username", None))
        CONFIG["cloudera_password"] = __SECRETS.get(domain, "cloudera_password",
                                                    fallback=defaults.get("cloudera_password", None))
        CONFIG["kerberos_username"] = __SECRETS.get(domain, "kerberos_username",
                                                    fallback=defaults.get("kerberos_username", None))
        CONFIG["kerberos_password"] = __SECRETS.get(domain, "kerberos_password",
                                                    fallback=defaults.get("kerberos_password", None))
        CONFIG["cf_api_version"] = __CONFIG.get(domain, "cf_api_version", fallback=defaults.get("cf_api_version", None))
    CONFIG["test_suite"] = test_suite
    if logged_response_body_length is not None:
        tap_logger.LOGGED_RESPONSE_BODY_LENGTH = logged_response_body_length
    if client_type is not None:
        CONFIG["client_type"] = client_type
    if logging_level is not None:
        tap_logger.set_level(logging_level)
    if repository is not None:
        CONFIG["repository"] = repository
    if database_url is not None:
        CONFIG["database_url"] = database_url
    if local_appstack is not None:
        CONFIG["local_appstack"] = local_appstack
    if disable_remote_logger is not None:
        CONFIG["remote_log_enabled"] = not disable_remote_logger
    if remote_logger_retry_count is not None:
        CONFIG["remote_logger_retry_count"] = remote_logger_retry_count
    if pushed_app_proxy is not None:
        CONFIG["pushed_app_proxy"] = pushed_app_proxy
    CONFIG["ref_org_name"] = ref_org_name if ref_org_name is not None else "trustedanalytics"
    CONFIG["ref_space_name"] = ref_space_name if ref_space_name is not None else "platform"
    CONFIG["test_run_id"] = test_run_id
    if kerberos is not None:
        CONFIG["kerberos"] = kerberos
    CONFIG["jumpbox_address"] = jumpbox_address
    CONFIG["elasticsearch_host"] = elasticsearch_host
    CONFIG["kubernetes"] = ensure_bool(kubernetes) if kubernetes is not None else False


def ensure_bool(value):
    """Ensurance that return value is always bool. Converts from string if necessary."""
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            raise Exception(str(value) + " is not 'true' or 'false' string!")

    raise Exception(str(type(value)) + " is not a string or bool type!")


def setup_admin_login(domain, defaults, admin_username=None, admin_password=None):

    admin_username = admin_username or os.environ.get("ADMIN_USERNAME") or \
                     __CONFIG.get(domain, "admin_username", fallback=defaults.get("admin_username"))

    CONFIG["admin_username"] = admin_username
    CONFIG["admin_password"] = admin_password or os.environ.get("ADMIN_PASSWORD") or \
                               __SECRETS.get(domain, admin_username, fallback=defaults.get(admin_username, None))


# update settings using default values
update_test_config(domain="daily.gotapaas.com",
                   client_type="console",
                   logged_response_body_length=1024,
                   logging_level="DEBUG",
                   repository="intel-data")
# update settings using environment variables (when tests are run with PyCharm runner)
update_test_config(domain=os.environ.get("TEST_ENVIRONMENT"),
                   client_type=os.environ.get("TEST_CLIENT_TYPE"),
                   logged_response_body_length=os.environ.get("LOGGED_RESPONSE_BODY_LENGTH"),
                   platform_version=os.environ.get("PLATFORM_VERSION", "master"),
                   database_url=os.environ.get("DATABASE_URL"),
                   kerberos=os.environ.get("KERBEROS"),
                   jumpbox_address=os.environ.get("JUMPBOX_ADDRESS"),
                   elasticsearch_host=os.environ.get("ELASTICSEARCH_HOST"),
                   kubernetes=os.environ.get("KUBERNETES"))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Platform API Automated Tests")
    parser.add_argument("-e", "--environment",
                        help="environment where tests are to be run, e.g. gotapaas.eu",
                        required=True)
    parser.add_argument("-s", "--suite",
                        default=None,
                        help="a group of tests to execute (directory or file path)")
    parser.add_argument("-t", "--tests",
                        default=None,
                        nargs="+",
                        help="only run tests that match any test names")
    parser.add_argument("-f", "--file",
                        default=None,
                        help="path to a file with a list of tests to execute")
    parser.add_argument("-v", "--platform-version",
                        default="master",
                        help="Platform version tag name")
    parser.add_argument("-p", "--priority",
                        default=[],
                        action="append",
                        type=lambda x: getattr(priority, x).markname,
                        help="Run subset of tests with given priority")
    parser.add_argument("-c", "--components",
                        default=[],
                        action="append",
                        type=lambda x: x.replace("-", "_"),
                        help="Limit tests to those which use specified components")
    parser.add_argument("--only-tagged",
                        default=[],
                        action="append",
                        help="Limit tests to those which are included in specified group")
    parser.add_argument("--not-tagged",
                        default=[],
                        action="append",
                        help="Limit tests to those which are not included in specified group")
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
    parser.add_argument("--repository",
                        choices=["intel-data", "trustedanalytics"],
                        default="intel-data",
                        help="Repository from which the applications source code is cloned.")
    parser.add_argument("--database-url",
                        default=None,
                        help="URL to database for storing test results")
    parser.add_argument("--local-appstack",
                        default=None)
    parser.add_argument("--admin-username",
                        default=None,
                        help="User with admin privileges to run tests")
    parser.add_argument("--admin-password",
                        default=None,
                        help="Admin user password")
    parser.add_argument("--reference-org",
                        default="trustedanalytics",
                        help="pass reference org")
    parser.add_argument("--reference-space",
                        default="platform",
                        help="pass reference space")
    parser.add_argument("--test-run-id",
                        help="used by platform-tests TAP application")
    parser.add_argument("--disable-remote-logger",
                        action='store_true',
                        help="Disable remote logger")
    parser.add_argument("--remote-logger-retry-count",
                        type=int,
                        help="Set number of retries for remote logger.")
    parser.add_argument("--kerberos",
                        action='store_true',
                        help="Pass this parameter if environment has kerberos.")
    parser.add_argument("--jumpbox-address",
                        default=None,
                        action='store_true',
                        help="Address of the jumpbox machine (jump.<domain> of empty)")
    parser.add_argument("--elasticsearch_host",
                        default=None,
                        help="Address of the elasticsearch service")
    parser.add_argument("--pushed-app-proxy",
                        default=None,
                        help="Proxy to be set in pushed app manifest, e.g. proxy-mu.intel.com (no port)")
    parser.add_argument("--kubernetes",
                        action='store_true',
                        help="Pass this parameter if environment has kubernetes.")
    return parser.parse_args()

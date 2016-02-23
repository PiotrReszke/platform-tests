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

import os
import unittest
import requests

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from constants.tap_components import TapComponent
from test_utils import config, get_logger, change_log_file_path


def flatten_test_suite(test_suite):
    """
    Return unittest.TestSuite with flattened test list (i.e. not containing other TestSuites).

    test_suite -- unittest.TestSuite object
    """
    if not isinstance(test_suite, unittest.TestSuite):
        raise TypeError("not a TestSuite", test_suite)
    tests = []
    for item in test_suite._tests:
        if isinstance(item, unittest.TestSuite):
            tests.extend(flatten_test_suite(item))
        else:
            tests.append(item)
    suite = unittest.TestSuite()
    suite.addTests(tests)
    suite.flattened = True
    return suite


def filter_test_suite(test_suite, filter_method):
    """
    Return unittest.TestSuite formed of those tests from test_suite for which filter_method returns True.

    test_suite -- unittest.TestSuite object
    filter_method -- callable which returns bool when applied to a ApiTestCase object
    """
    if not isinstance(test_suite, unittest.TestSuite):
        raise TypeError("not a TestSuite", test_suite)
    if not getattr(test_suite, "flattened", False):
        test_suite = flatten_test_suite(test_suite)
    tests = [t for t in test_suite._tests if filter_method(t)]
    suite = unittest.TestSuite()
    suite.addTests(tests)
    return suite


if __name__ == "__main__":

    logger = get_logger("run_tests")

    # parse settings passed from command line and update config
    args = config.parse_arguments()
    if not is_running_under_teamcity():
        log_dir = args.log_file_directory
        os.makedirs(log_dir, exist_ok=True)
        change_log_file_path(args.log_file_directory)
    config.update_test_config(client_type=args.client_type,
                              domain=args.environment,
                              proxy=args.proxy,
                              logged_response_body_length=args.logged_response_body_length,
                              logging_level=args.logging_level,
                              platform_version=args.platform_version)
    for key in ["domain", "admin_username", "client_type", "proxy", "ssl_validation", "platfom_version"]:
        logger.info("{}={}".format(key, config.CONFIG.get(key)))

    # select group of tests to run
    loader = unittest.TestLoader()
    loaded_tests = None
    if args.test is not None:
        loader.testMethodPrefix = args.test
    test_dir = "tests"
    if args.suite is not None:
        test_dir = os.path.join("tests", args.suite)
    if os.path.isfile(test_dir):
        test_dir, file_name = os.path.split(test_dir)
        loaded_tests = loader.discover(test_dir, file_name)
    elif os.path.isdir(test_dir):
        loaded_tests = loader.discover(test_dir)
    else:
        raise NotADirectoryError("Directory {} doesn't exists".format(args.suite))
    if loaded_tests is not None and loaded_tests.countTestCases() is 0:
        raise Exception("No tests found.")

    # check if environment is up and running
    try:
        domain = config.CONFIG["domain"]
        verify = config.CONFIG["ssl_validation"]
        console_endpoint = "https://console.{}".format(domain)
        cf_endpoint = "https://api.{}/v2/info".format(domain)
        requests.get(console_endpoint, verify=verify).raise_for_status()
        requests.get(cf_endpoint, verify=verify).raise_for_status()
    except requests.HTTPError as e:
        logger.error("Environment {} is unavailable - status {}".format(e.response.url, e.response.status_code))
        raise

    # run tests
    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestSuite()
    suite.addTests(loaded_tests)

    # apply filters - priority and requested components
    suite = filter_test_suite(suite, lambda x: x.priority <= args.priority)
    if args.components != []:
        components = [getattr(TapComponent, c) for c in args.components]
        suite = filter_test_suite(suite, lambda x: bool(set(x.components) & set(components)))

    runner.run(suite)

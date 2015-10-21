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

from test_utils import config, get_logger


logger = get_logger("run tests")


if __name__ == "__main__":

    # parse settings passed from command line and update config
    args = config.parse_arguments()
    config.update_test_config(client_type=args.client_type,
                              domain=args.environment,
                              proxy=args.proxy,
                              logged_response_body_length=args.logged_response_body_length)
    for key in ["domain", "admin_username", "client_type", "proxy", "ssl_validation"]:
        logger.info("{}={}".format(key, config.CONFIG[key]))

    # select group of tests to run
    if args.test is None:
        test_dir = "tests"
    else:
        test_dir = os.path.join("tests", args.test)
        if not os.path.exists(test_dir):
            raise NotADirectoryError("Directory {} doesn't exists".format(args.test))

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
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.discover(test_dir))
    runner.run(suite)

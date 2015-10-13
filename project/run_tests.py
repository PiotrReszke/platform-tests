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
import sys

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from test_utils import config, get_logger


logger = get_logger("run tests")



if __name__ == "__main__":

    # parse settings passed from command line
    args = config.parse_arguments()

    config.update_test_settings(client_type=args.client_type,
                                test_environment=args.environment,
                                test_username=args.username,
                                proxy=args.proxy,
                                disable_ssl_validation=args.disable_ssl_validation)
    for key in ["TEST_ENVIRONMENT", "TEST_USERNAME", "TEST_CLIENT_TYPE", "TEST_PROXY", "TEST_DISABLE_SSL_VALIDATION"]:
        logger.info("{}={}".format(key, config.TEST_SETTINGS[key]))

    if args.test is None:
        test_dir = "tests"
    else:
        test_dir = "tests/" + args.test
        if not os.path.exists(test_dir):
            raise NotADirectoryError("Directory {} doesn't exists".format(args.test))

    # check if environment is up and running
    try:
        scheme = config.get_config_value("login.do_scheme")
        requests.get(scheme + "://console." + config.get_config_value("api_endpoint")).raise_for_status()
        requests.get(scheme + "://" + config.get_config_value("cf_endpoint") + "/v2/info").raise_for_status()
    except requests.HTTPError as e:
            logger.error("Environment {} is unavailable - status {}".format(e.response.url, e.response.status_code))
            sys.exit(1)
    else:
        # run tests
        if is_running_under_teamcity():
            runner = TeamcityTestRunner()
        else:
            runner = unittest.TextTestRunner(verbosity=3)
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        suite.addTests(loader.discover(test_dir))
        runner.run(suite)

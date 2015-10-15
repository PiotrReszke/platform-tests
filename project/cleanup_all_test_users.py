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
import re

from test_utils import get_logger, config
from objects import User

TEST_USER_PATTERN = "intel\.data\.tests\+[0-9]{10}.*@gmail\.com$"
logger = get_logger("user cleanup")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Test user cleanup script")
    parser.add_argument("-e",
                        "--environment",
                        default=None,
                        help="Environment on which cleanup shall be performed, e.g. gotapaas.eu")
    args = parser.parse_args()
    config.update_test_config(domain=args.environment)

    all_users = User.cf_api_get_all_users()
    test_users = [u for u in all_users if re.match(TEST_USER_PATTERN, u.username or "")]
    logger.info("Deleting {} users: {}".format(len(test_users), test_users))
    failed_to_delete = User.cf_api_delete_users_from_list(test_users, async=False)
    logger.info("Deleted {} users. Could not delete {}: {}".format(
        len(test_users) - len(failed_to_delete), len(failed_to_delete), failed_to_delete
    ))

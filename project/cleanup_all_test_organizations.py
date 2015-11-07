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

from test_utils import get_logger, config, UnexpectedResponseError
from objects import Organization


TEST_ORG_PATTERN = "(^|^new-)test_org_[0-9]{8}_[0-9]{6}_[0-9]{6}$"
logger = get_logger("organization cleanup")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Test org cleanup script")
    parser.add_argument("-e",
                        "--environment",
                        default=None,
                        help="environment where tests are to be run, e.g. gotapaas.eu")
    args = parser.parse_args()
    config.update_test_config(domain=args.environment)

    all_orgs = Organization.cf_api_get_list()
    test_orgs = [o for o in all_orgs if re.match(TEST_ORG_PATTERN, o.name)]
    logger.info("Deleting {} organizations:\n{}".format(len(test_orgs), "\n".join([str(o) for o in test_orgs])))
    failed_to_delete = []
    for test_org in test_orgs:
        try:
            test_org.cf_api_delete()
        except UnexpectedResponseError as e:
            failed_to_delete.append(test_org)
            logger.warning("Failed to delete {}: {}".format(test_org, e))
    logger.info("Could not delete {} orgs:\n{}".format(len(failed_to_delete), "\n".join(failed_to_delete)))


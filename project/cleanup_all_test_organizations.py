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

import re

from test_utils import get_logger
from objects import Organization


TEST_ORG_PATTERN = "(^|^new-)test_org_[0-9]{8}_[0-9]{6}_[0-9]{6}$"
logger = get_logger("organization cleanup")


if __name__ == "__main__":

    all_orgs = Organization.cf_api_get_list()
    test_orgs = [o for o in all_orgs if re.match(TEST_ORG_PATTERN, o.name)]
    logger.info("Deleting {} organizations: {}".format(len(test_orgs), test_orgs))
    failed_to_delete = []
    for org in test_orgs:
        try:
            org.cf_api_delete()
        except Exception as e:
            failed_to_delete.append(org)
            logger.error("Could not delete {}\n{}\n".format(org, e))

    logger.info("Deleted {} orgs. Could not delete {}: {}".format(
        len(test_orgs) - len(failed_to_delete), len(failed_to_delete), failed_to_delete
    ))

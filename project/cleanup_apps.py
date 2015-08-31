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

# This script can be use in order to deleting application according to specific pattern name.

import argparse
import re

from test_utils import get_logger
from test_utils.cli import cloud_foundry as cf
from test_utils.objects import Application, Organization

logger = get_logger("application cleanup")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Platform API Automated Tests")
    parser.add_argument("-p",
                        "--pattern",
                        help="application pattern name for deleting")
    parser.add_argument("-o",
                        "--organization",
                        default="seedorg",
                        help="organization in which appliction have been pushed")
    parser.add_argument("-s",
                        "--space",
                        default="seedspace",
                        help="space in which appliction have been pushed")
    args = parser.parse_args()
    pattern = args.pattern

    organization, space = Organization.get_org_and_space_by_name(args.organization, args.space)

    apps = Application.cf_api_get_list(space.guid)
    apps_to_delete = [app for app in apps if re.match(pattern, app.name)]
    logger.info("Deleting {} applications with pattern: {}".format(len(apps_to_delete), pattern))
    for app in apps_to_delete:
        try:
            cf.cf_delete(app.name)
        except Exception as e:
            logger.error("Could not delete {}".format(app.name))

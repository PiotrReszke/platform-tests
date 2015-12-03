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

from test_utils import get_logger, config, UnexpectedResponseError, platform_api_calls as api
from objects import Organization, User, Transfer, DataSet

TEST_ORG_PATTERN = "(^|^new-)test_org_[0-9]{8}_[0-9]{6}_[0-9]{6}$"
TEST_USER_PATTERN = "^intel\.data\.tests\+[0-9]{10}.*@gmail\.com$"
TEST_USER_INVITATION_PATTERN = "^intel\.data\.tests\+[0-9]{10}.*@gmail\.com$"
TEST_TRANSFER = "test_transfer[0-9]{8}_[0-9]{6}_[0-9]{6}$"
TEST_DATA_SET = "test_transfer[0-9]{8}_[0-9]{6}_[0-9]{6}$"


logger = get_logger("test data cleanup")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Test org cleanup script")
    parser.add_argument("-e",
                        "--environment",
                        default=None,
                        help="environment where tests are to be run, e.g. gotapaas.eu")
    args = parser.parse_args()
    config.update_test_config(domain=args.environment)

    all_orgs = Organization.cf_api_get_list()
    all_data_set = DataSet.api_get_list(org_list=all_orgs)
    test_data_sets = [d for d in all_data_set if re.match(TEST_DATA_SET, d.title)]
    logger.info("Deleting {} data sets:\n{}".format(len(test_data_sets), "\n".join([str(o) for o in test_data_sets])))
    failed_to_delete = []
    for test_data_set in test_data_sets:
        try:
            test_data_set.api_delete()
        except UnexpectedResponseError as e:
            failed_to_delete.append(test_data_set)
            logger.warning("Failed to delete {}: {}".format(test_data_set, e))
    logger.info("Deleted {} data sets. Could not delete {}:\n{}".format(len(test_data_sets) - len(failed_to_delete),
                                                                        len(failed_to_delete),
                                                                        "\n".join([str(ds) for ds in failed_to_delete])))

    all_transfer = Transfer.api_get_list(all_orgs)
    test_transfers = [t for t in all_transfer if re.match(TEST_TRANSFER, t.title)]
    logger.info("Deleting {} transfers:\n{}".format(len(test_transfers), "\n".join([str(o) for o in test_transfers])))
    failed_to_delete = []
    for test_transfer in test_transfers:
        try:
            test_transfer.api_delete()
        except UnexpectedResponseError as e:
            failed_to_delete.append(test_transfer)
            logger.warning("Failed to delete {}: {}".format(test_transfer, e))
    logger.info("Deleted {} transfers. Could not delete {}:\n{}".format(len(test_transfers) - len(failed_to_delete),
                                                                        len(failed_to_delete),
                                                                        "\n".join([str(t) for t in failed_to_delete])))

    test_orgs = [o for o in all_orgs if re.match(TEST_ORG_PATTERN, o.name)]
    logger.info("Deleting {} organizations:\n{}".format(len(test_orgs), "\n".join([str(o) for o in test_orgs])))
    failed_to_delete = []
    for test_org in test_orgs:
        try:
            test_org.cf_api_delete()
        except UnexpectedResponseError as e:
            failed_to_delete.append(test_org)
            logger.warning("Failed to delete {}: {}".format(test_org, e))
    logger.info("Deleted {} organizations. Could not delete {} orgs:\n{}".format(len(test_orgs) - len(failed_to_delete),
                                                                                 len(failed_to_delete),
                                                                                 "\n".join([str(o) for o in
                                                                                            failed_to_delete])))

    all_users = User.cf_api_get_all_users()
    test_users = [u for u in all_users if re.match(TEST_USER_PATTERN, u.username or "")]  # there is a user without username
    logger.info("Deleting {} users:\n{}".format(len(test_users), "\n".join([str(u) for u in test_users])))
    failed_to_delete = []
    for test_user in test_users:
        try:
            test_user.cf_api_delete()
        except UnexpectedResponseError as e:
            failed_to_delete.append(test_user)
            logger.warning("Failed to delete {}: {}".format(test_user, e))
    logger.info("Deleted {} users. Could not delete {} users:\n{}".format(len(test_users) - len(failed_to_delete),
                                                                          len(failed_to_delete),
                                                                          "\n".join([str(u) for u in failed_to_delete])))

    all_users_pending_invitations = User.api_get_pending_invitations()
    test_users_invitations = [i for i in all_users_pending_invitations if re.match(TEST_USER_INVITATION_PATTERN, i)]
    logger.info("Deleting {} users pending invitations:\n{}".format(len(test_users_invitations),
                                                                    "\n".join([str(i) for i in test_users_invitations])))
    failed_to_delete = []
    for test_user_invitation in test_users_invitations:
        try:
            User.api_delete_user_invitation(test_user_invitation)
        except UnexpectedResponseError as e:
            failed_to_delete.append(test_user_invitation)
            logger.warning("Failed to delete {}: {}".format(test_user_invitation, e))
    logger.info("Deleted {} users pending invitations. Could not delete {}:\n{}".format(
        len(test_users_invitations) - len(failed_to_delete), len(failed_to_delete),
        "\n".join([str(i) for i in failed_to_delete])))

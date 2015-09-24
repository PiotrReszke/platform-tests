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

import time
import unittest

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import User, Organization, Space


class BaseTestSpaceUsersClass(ApiTestCase):

    SPACE_ROLES = ("managers", "auditors", "developers")

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.test_org = Organization.api_create()

    def setUp(self):
        self.test_space = Space.api_create(self.test_org)

    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()

    def _assert_user_in_space_with_roles(self, expected_user, space_guid):
        space_users = User.api_get_list_via_space(space_guid)
        space_user = next((user for user in space_users if user.guid == expected_user.guid), None)
        self.assertIsNotNone(space_user, "{} was not found in space {}".format(expected_user, space_guid))
        space_user_roles = space_user.space_roles.get(space_guid)
        expected_roles = expected_user.space_roles.get(space_guid)
        self.assertEqual(space_user_roles, expected_roles, "{} space roles are not equal".format(expected_user))

    def _assert_user_not_in_space(self, expected_user, space_guid):
        space_users = User.api_get_list_via_space(space_guid)
        user_who_should_not_be_in_space = next((user for user in space_users if user.guid == expected_user.guid), None)
        self.assertIsNone(user_who_should_not_be_in_space, "Unexpectedly, {} was found in space".format(expected_user))


class GetSpaceUsers(BaseTestSpaceUsersClass):

    def test_get_user_list_from_deleted_space(self):
        self.test_space.cf_api_delete()
        self.assertRaisesUnexpectedResponse(404, "Not Found", User.api_get_list_via_space, self.test_space.guid)


class AddSpaceUser(BaseTestSpaceUsersClass):

    def test_add_existing_users_with_one_role(self):
        test_users = [User.api_create_by_adding_to_organization(self.test_org.guid)
                      for _ in range(len(self.SPACE_ROLES))]
        space_user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertEqual(len(space_user_list), 0, "Retrieved user list should be empty")
        for test_user, role in zip(test_users, self.SPACE_ROLES):
            test_user.api_add_to_space(self.test_space.guid, self.test_org.guid, roles=(role,))
        space_user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertCountEqual(space_user_list, test_users, "User lists are not equal.")
        for expected_user in test_users:
            self._assert_user_in_space_with_roles(expected_user, self.test_space.guid)

    @unittest.expectedFailure
    def test_add_existing_user_without_roles(self):
        """DPNG-2281 It's possible to add user to space without any roles using API"""
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        self.assertRaisesUnexpectedResponse(400, "???", test_user.api_add_to_space, self.test_space.guid,
                                            self.test_org.guid, roles=())
        self._assert_user_not_in_space(test_user, self.test_space.guid)

    def test_add_existing_user_with_all_available_roles(self):
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid, roles=self.SPACE_ROLES)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_add_non_existing_user_to_space(self):
        """DPNG-2287 Cannot register as a new user added to space"""
        new_user = User.api_create_by_adding_to_space(self.test_org.guid, self.test_space.guid)
        self._assert_user_in_space_with_roles(new_user, self.test_space.guid)


class UpdateSpaceUser(BaseTestSpaceUsersClass):

    @unittest.expectedFailure
    def test_change_username(self):
        """DPNG-2247 Trying to change username ends with http 500 status error"""
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        new_name = "new_" + test_user.username
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        test_user.api_update_via_space(self.test_org.guid, self.test_space.guid, new_username=new_name)
        updated_user = User.api_get_list_via_space(self.test_space.guid)[0]
        self.assertEqual(updated_user.username, new_name, "Name was not updated")

    @unittest.expectedFailure
    def test_cannot_change_space_user_username_to_one_that_already_exists(self):
        """DPNG-2247 Trying to change username ends with http 500 status error"""
        updated_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        updated_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        self.assertRaisesUnexpectedResponse(400, "???", updated_user.api_update_via_space, self.test_org.guid,
                                            self.test_space.guid, new_username=test_user.username)
        self._assert_user_in_space_with_roles(updated_user, self.test_space.guid)

    @unittest.expectedFailure
    def test_cannot_change_username_to_a_non_email(self):
        """DPNG-2247 Trying to change username ends with http 500 status error"""
        new_name = "wrong_username_{}".format(time.time())
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        self.assertRaisesUnexpectedResponse(400, "???", self.test_org.guid, self.test_space.guid,
                                            new_username=new_name)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_change_user_role(self):
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        new_roles = ("developers",)
        test_user.api_update_via_space(self.test_org.guid, self.test_space.guid, new_roles=new_roles)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_try_change_role_to_not_existing(self):
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        new_roles = ("wrong_role",)
        self.assertRaisesUnexpectedResponse(400, "Bad Request", test_user.api_update_via_space, self.test_org.guid,
                                            self.test_space.guid, new_roles=new_roles)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_delete_user_roles_while_in_space(self):  # deleting all roles deletes user from the space
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        test_user.api_update_via_space(self.test_org.guid, self.test_space.guid, new_roles=())
        self._assert_user_not_in_space(test_user, self.test_space.guid)


class DeleteSpaceUser(BaseTestSpaceUsersClass):

    def test_delete_user_from_space(self):
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)
        test_user.api_delete_from_space(self.test_space.guid)
        self._assert_user_not_in_space(test_user, self.test_space.guid)

    @unittest.expectedFailure
    def test_delete_user_which_is_not_in_space(self):
        """DPNG-2293 Deleting from space a user which is not in this space does not return any error"""
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        self.assertRaisesUnexpectedResponse(404, "???", test_user.api_delete_from_space, self.test_space.guid)

    def test_that_user_exist_in_org_after_deletion_from_space(self):
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        test_user.api_delete_from_space(self.test_space.guid)
        org_user_list = User.api_get_list_via_organization(self.test_org.guid)
        self.assertInList(test_user, org_user_list, "{} was not found in organization.".format(test_user))


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

import unittest

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import User, Organization, Space


class SpaceUsers(ApiTestCase):

    SPACE_ROLES = ("managers", "auditors", "developers")

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create a test organization")
        cls.test_org = Organization.api_create()

    def setUp(self):
        self.step("Create a test space")
        self.test_space = Space.api_create(self.test_org)

    @classmethod
    def tearDownClass(cls):
        User.cf_api_tear_down_test_users()
        Organization.cf_api_tear_down_test_orgs()

    def _assert_user_in_space_with_roles(self, expected_user, space_guid):
        self.step("Check that the user is on the list of space users")
        space_users = User.api_get_list_via_space(space_guid)
        self.assertInList(expected_user, space_users)
        space_user = next(user for user in space_users if user.guid == expected_user.guid)
        self.step("Check that the user has expected space roles")
        space_user_roles = space_user.space_roles.get(space_guid)
        expected_roles = expected_user.space_roles.get(space_guid)
        self.assertEqual(space_user_roles, expected_roles, "{} space roles are not equal".format(expected_user))

    def _assert_user_not_in_space(self, expected_user, space_guid):
        self.step("Check that the user is not on the space user list")
        space_users = User.api_get_list_via_space(space_guid)
        user_who_should_not_be_in_space = next((user for user in space_users if user.guid == expected_user.guid), None)
        self.assertIsNone(user_who_should_not_be_in_space, "Unexpectedly, {} was found in space".format(expected_user))

    def test_get_user_list_from_deleted_space(self):
        self.step("Delete the space")
        self.test_space.cf_api_delete()
        self.step("Check that retrieving list of users in the deleted space returns an error")
        self.assertRaisesUnexpectedResponse(404, "Not Found", User.api_get_list_via_space, self.test_space.guid)

    def test_add_existing_users_with_one_role(self):
        for space_role in self.SPACE_ROLES:
            space_role = (space_role,)
            with self.subTest(space_role=space_role):
                self.step("Create new platform user by adding to the organization")
                test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
                self.step("Add the user to space with role {}".format(space_role))
                test_user.api_add_to_space(self.test_space.guid, self.test_org.guid, roles=space_role)
                self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_add_existing_user_without_roles(self):
        """DPNG-2281 It's possible to add user to space without any roles using API"""
        self.step("Create new platform user by adding to the organization")
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        self.step("Check that attempt to add user to space with no roles returns an error")
        self.assertRaisesUnexpectedResponse(409, "You must have at least one role", test_user.api_add_to_space,
                                            self.test_space.guid, self.test_org.guid, roles=())
        self._assert_user_not_in_space(test_user, self.test_space.guid)

    def test_add_existing_user_with_all_available_roles(self):
        self.step("Create new platform user by adding to the organization")
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        self.step("Add the user to space with roles {}".format(self.SPACE_ROLES))
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid, roles=self.SPACE_ROLES)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_add_non_existing_user_to_space(self):
        """DPNG-2287 Cannot register as a new user added to space"""
        self.step("Create new platform user by adding them to space")
        new_user = User.api_create_by_adding_to_space(self.test_org.guid, self.test_space.guid)
        self._assert_user_in_space_with_roles(new_user, self.test_space.guid)

    @unittest.expectedFailure
    def test_cannot_change_username(self):
        """DPNG-2247 user-management documentation allows for updating username for org and space user"""
        self.step("Create new platform user by adding to the space")
        test_user = User.api_create_by_adding_to_space(org_guid=self.test_org.guid, space_guid=self.test_space.guid)
        new_name = "new_" + test_user.username
        self.step("Check that attempt to update the user's username returns an error")
        self.assertRaisesUnexpectedResponse("400", "Bad Request", test_user.api_update_via_space, self.test_org.guid,
                                            self.test_space.guid, new_username=new_name)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_change_user_role(self):
        initial_roles = [self.SPACE_ROLES[1]]
        new_roles = [self.SPACE_ROLES[2]]
        self.step("Create new platform user by adding to space with roles {}".format(initial_roles))
        test_user = User.api_create_by_adding_to_space(org_guid=self.test_org.guid, space_guid=self.test_space.guid,
                                                       roles=initial_roles)
        self.step("Update the user, change their role to {}".format(new_roles))
        test_user.api_update_via_space(self.test_org.guid, self.test_space.guid, new_roles=new_roles)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_cannot_change_role_to_invalid_one(self):
        initial_roles = [self.SPACE_ROLES[1]]
        new_roles = ("wrong_role",)
        self.step("Create new platform user by adding to space with roles {}".format(initial_roles))
        test_user = User.api_create_by_adding_to_space(org_guid=self.test_org.guid, space_guid=self.test_space.guid,
                                                       roles=initial_roles)
        self.step("Check that updating space user roles to invalid ones returns an error")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", test_user.api_update_via_space, self.test_org.guid,
                                            self.test_space.guid, new_roles=new_roles)
        self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_delete_user_roles_while_in_space(self):
        # deleting all roles deletes user from the space, but the user remains in the organization
        self.step("Create new platform user by adding to space")
        test_user = User.api_create_by_adding_to_space(org_guid=self.test_org.guid, space_guid=self.test_space.guid)
        self.step("Update the user, removing all space roles")
        test_user.api_update_via_space(self.test_org.guid, self.test_space.guid, new_roles=())
        self._assert_user_not_in_space(test_user, self.test_space.guid)
        self.step("Check that the user is still in the organization")
        org_users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        self.assertInList(test_user, org_users, "User is not in the organization")

    def test_delete_user_from_space(self):
        self.step("Create a new platform user by adding to the organization")
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        self.step("Add the user to space")
        test_user.api_add_to_space(self.test_space.guid, self.test_org.guid)
        self.step("Delete the user from space")
        test_user.api_delete_from_space(self.test_space.guid)
        self._assert_user_not_in_space(test_user, self.test_space.guid)
        self.step("Check that the user is still in the organization")
        org_users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        self.assertInList(test_user, org_users, "User is not in the organization")

    def test_delete_user_which_is_not_in_space(self):
        """DPNG-2293 Deleting from space a user which is not in this space does not return any error"""
        self.step("Create a new platform user by adding to the organization")
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        self.step("Check that deleting the user from space they are not in returns an error")
        self.assertRaisesUnexpectedResponse(404, "The user is not in given space", test_user.api_delete_from_space,
                                            self.test_space.guid)

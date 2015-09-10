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

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import User, Organization, Space


class TestSpaceUsers(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.organization = Organization.api_create()

    def setUp(self):
        self.test_space = Space.api_create(self.organization)

    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()

    def test_get_user_list_from_not_existing_space(self):
        """Testing GET '/rest/spaces/{space_guid}/users' API method"""
        self.test_space.cf_api_delete()
        self.assertRaisesUnexpectedResponse(404, None, User.api_get_list_via_space, self.test_space.guid)

    def test_add_space_users_and_get_user_list_from_space(self):
        """Add new users to space and then retrieve them"""
        roles = ("managers", "auditors", "developers")
        test_users = [User.api_create_by_adding_to_organization(self.organization.guid) for _ in range(3)]
        space_user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertEqual(len(space_user_list), 0, "Retrieved user list should be empty")
        for i in range(3):
            test_users[i].api_add_to_space(self.test_space.guid, self.organization.guid, roles=(roles[i],))
        space_user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertCountEqual(space_user_list, test_users, "User lists are not equal.")
        for user in space_user_list:
            added_user_space_role = tuple(user.space_roles.get(self.test_space.guid))
            test_user_space_roles = tuple(next((test_user.space_roles.get(
                self.test_space.guid) for test_user in test_users if test_user.guid == user.guid)))
            self.assertEqual(added_user_space_role, test_user_space_roles,
                             "User {} roles are not equal".format(user.guid))

    def test_delete_user_from_space(self):
        """Testing DELETE '/rest/spaces/{space_guid}/users/{user_guid}' API method"""
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid)
        space_user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertEqual(len(space_user_list), 1, "Retrieved list contains {} users - expected 1"
                         .format(len(space_user_list)))
        test_user.api_delete_via_space(self.test_space.guid)
        space_user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertEqual(len(space_user_list), 0, "User was not removed from space")

    def test_change_username(self):
        """Testing PUT '/rest/spaces/{space_guid}/users/{user_guid}' API method"""
        new_name = User.get_default_username()
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        self.assertNotEqual(test_user.username, new_name, "Names are the same - should be different")
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid)
        test_user.api_update_via_space(self.organization.guid, self.test_space.guid, new_username=new_name)
        updated_user = User.api_get_list_via_space(self.test_space.guid)[0]
        self.assertEqual(updated_user.username, new_name, "Name was not updated")

    def test_change_user_role(self):
        """Testing PUT '/rest/spaces/{space_guid}/users/{user_guid}' API method"""
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid)
        new_roles = ("developers",)
        test_user.api_update_via_space(self.organization.guid, self.test_space.guid, new_roles=new_roles)
        updated_user = User.api_get_list_via_space(self.test_space.guid)[0]
        self.assertEqual(tuple(updated_user.space_roles.get(self.test_space.guid)), new_roles, "Roles were not updated")

    def test_try_change_username_to_existing(self):
        """Testing PUT '/rest/spaces/{space_guid}/users/{user_guid}' API method"""
        test_user_a = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user_b = User.api_create_by_adding_to_organization(self.organization.guid)
        self.assertNotEqual(test_user_a.username, test_user_b.username, "User names are the same")
        test_user_a.api_add_to_space(self.test_space.guid, self.organization.guid)
        test_user_b.api_add_to_space(self.test_space.guid, self.organization.guid)
        self.assertRaisesUnexpectedResponse(400, None, test_user_a.api_update_via_space, self.organization.guid,
                                            self.test_space.guid, new_username=test_user_b.username)
        users_after_changes = User.api_get_list_via_space(self.test_space.guid)
        self.assertNotEqual(users_after_changes[0].username, users_after_changes[1].username)

    def test_try_change_role_to_not_existing(self):
        """Testing PUT '/rest/spaces/{space_guid}/users/{user_guid}' API method"""
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid)
        new_roles = ("wrong_role",)
        self.assertRaisesUnexpectedResponse(400, None, test_user.api_update_via_space, self.organization.guid,
                                            self.test_space.guid, new_roles=new_roles)
        user_after_changes = User.api_get_list_via_space(self.test_space.guid)[0]
        self.assertNotEqual(user_after_changes.space_roles.get(self.test_space.guid), new_roles, "Roles were updated")

    def test_delete_user_which_is_not_in_space(self):
        """Testing DELETE '/rest/spaces/{space_guid}/users/{user_guid}' API method"""
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        self.assertRaisesUnexpectedResponse(404, None, test_user.api_delete_via_space, self.test_space.guid)

    def test_that_user_exist_in_org_after_deletion_from_space(self):
        """Testing DELETE '/rest/spaces/{space_guid}/users/{user_guid}' API method"""
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid)
        test_user.api_delete_via_space(self.test_space.guid)
        org_user_list = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(test_user, org_user_list, "User was not found in organization.")

    def test_change_username_to_a_non_email(self):
        """Testing PUT '/rest/spaces/{space_guid}/users/{user_guid}' API method"""
        new_name = "wrong_username_{}".format(time.time())
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid)
        test_user.api_update_via_space(self.organization.guid, self.test_space.guid, new_username=new_name)
        updated_user = User.api_get_list_via_space(self.test_space.guid)[0]
        self.assertNotEqual(updated_user.username, new_name, "Name was updated")

    def test_add_user_without_roles(self):
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid, roles=())
        user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertNotInList(test_user, user_list, "User is in space")

    def test_add_user_with_all_available_roles(self):
        test_roles = ("managers", "auditors", "developers")
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid, roles=test_roles)
        added_user = User.api_get_list_via_space(self.test_space.guid)[0]
        self.assertEqual(tuple(added_user.space_roles[self.test_space.guid]), test_roles, "Roles were not updated.")

    def test_delete_user_roles_while_in_space(self):
        test_user = User.api_create_by_adding_to_organization(self.organization.guid)
        test_user.api_add_to_space(self.test_space.guid, self.organization.guid)
        test_user.api_update_via_space(self.organization.guid, self.test_space.guid, new_roles=())
        user_list = User.api_get_list_via_space(self.test_space.guid)
        self.assertNotInList(test_user, user_list, "User is in space")

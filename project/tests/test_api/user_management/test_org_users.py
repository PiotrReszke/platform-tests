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

from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger, platform_api_calls as api
from objects import Organization, User


logger = get_logger("test org users")


class BaseOrgUserClass(ApiTestCase):

    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]

    @classmethod
    def tearDownClass(cls):
        User.cf_api_tear_down_test_users()
        Organization.cf_api_tear_down_test_orgs()

    def _assert_user_in_org_and_roles(self, invited_user, org_guid, expected_roles):
        self.step("Check that the user is in the organization with expected roles ({}).".format(expected_roles))
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertInList(invited_user, org_users, "Invited user is not on org users list")
        invited_user_roles = list(invited_user.org_roles.get(org_guid, []))
        self.assertUnorderedListEqual(invited_user_roles, list(expected_roles),
                                      "User's roles in org: {}, expected {}".format(invited_user_roles,
                                                                                    list(expected_roles)))

    def _assert_user_not_in_org(self, user, org_guid):
        self.step("Check that the user is not in the organization.")
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertNotInList(user, org_users, "User is among org users, although they shouldn't")


class AddExistingUserToOrganization(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs, User.cf_api_tear_down_test_users)
    def setUpClass(cls):
        cls.step("Onboard test user")
        cls.test_user, cls.test_org = User.api_onboard()
        cls.test_client = cls.test_user.login()

    def test_add_existing_user_with_no_roles(self):
        invited_user = self.test_user
        expected_roles = []
        self.step("Create an organization.")
        org = Organization.api_create()
        self.step("Add a platform user to organization with no roles.")
        invited_user.api_add_to_organization(org_guid=org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_existing_user_one_role(self):
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                invited_user = self.test_user
                self.step("Create an organization.")
                org = Organization.api_create()
                self.step("Add a platform user to organization with roles {}.".format(expected_roles))
                invited_user.api_add_to_organization(org.guid, roles=expected_roles)
                self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_existing_user_all_roles(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = self.ALL_ROLES
        self.step("Add a platform user to organization with roles {}.".format(expected_roles))
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_user_which_is_already_in_org_with_the_same_role(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["manager"]
        self.step("Add a platform user to organization with roles {}.".format(expected_roles))
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self.step("Add the same user to the same organization with the same roles")
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_user_which_is_already_in_org_with_different_role(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        roles_0 = User.ORG_ROLES["manager"]
        roles_1 = User.ORG_ROLES["auditor"]
        expected_roles = roles_0 | roles_1  # adding user with a new role results in the user having sum of the roles
        self.step("Add a platform user to organization with roles {}.".format(roles_0))
        invited_user.api_add_to_organization(org.guid, roles=roles_0)
        self.step("Add the same user to the same organization with roles {}".format(roles_1))
        invited_user.api_add_to_organization(org.guid, roles=roles_1)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_org_manager_adds_existing_user(self):
        invited_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                self.step("Create an organization.")
                org = Organization.api_create()
                self.step("Add a platform user as manager to the organization.")
                inviting_user.api_add_to_organization(org.guid, roles=User.ORG_ROLES["manager"])
                self.step("The new manager adds a platform user to the organization.")
                invited_user.api_add_to_organization(org.guid, roles=expected_roles, client=inviting_client)
                self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_non_manager_cannot_add_existing_user_to_org(self):
        """DPNG-2271 /org/:org_guid/users returns different error messages for similar invalid requests"""
        invited_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(inviting_user_role=non_manager_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                self.step("Create an organization.")
                org = Organization.api_create()
                self.step("Add a platform user as non-manager to the organization.")
                inviting_user.api_add_to_organization(org.guid, roles=non_manager_roles)
                expected_roles = User.ORG_ROLES["auditor"]
                self.step("Check that the non-manager is able to add a platform user to the org")
                self.assertRaisesUnexpectedResponse(403, "Forbidden", invited_user.api_add_to_organization,
                                                    org_guid=org.guid, roles=expected_roles, client=inviting_client)
                self._assert_user_not_in_org(invited_user, org.guid)

    def test_user_cannot_add_themselves_to_org(self):
        invited_user, inviting_client = self.test_user, self.test_client
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["auditor"]
        self.step("Check that a platform user is not able to add themselves to the organization")
        self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                            invited_user.api_add_to_organization, org_guid=org.guid,
                                            roles=expected_roles, client=inviting_client)
        self._assert_user_not_in_org(invited_user, org.guid)

    @unittest.expectedFailure
    def test_cannot_add_existing_user_to_non_existing_org(self):
        """DPNG-2270 Using incorrect guid format in request results in Internal Server Error"""
        invited_user = self.test_user
        invalid_org_guid = "this-org-guid-is-not-correct"
        roles = self.ALL_ROLES
        self.step("Check that adding user to organization using invalid org guid raises an error")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", invited_user.api_add_to_organization,
                                            org_guid=invalid_org_guid, roles=roles)

    def test_cannot_add_existing_user_with_incorrect_role(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        invalid_role = ["incorrect-role"]
        self.step("Check that it is not possible to add user to the organization with role {}".format(invalid_role))
        self.assertRaisesUnexpectedResponse(400, "Bad Request", invited_user.api_add_to_organization, org_guid=org.guid,
                                            roles=invalid_role)
        self._assert_user_not_in_org(invited_user, org.guid)


class AddNewUserToOrganization(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs, User.cf_api_tear_down_test_users)
    def setUpClass(cls):
        cls.step("Onboard test user")
        cls.test_user, cls.test_org = User.api_onboard()
        cls.test_client = cls.test_user.login()

    def test_add_new_user_with_no_roles(self):
        """DPNG-2540 Cannot add new user to organization without roles"""
        org = self.test_org
        expected_roles = []
        self.step("Create new user by adding to an organization with no roles")
        invited_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_new_user_one_role(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        org = self.test_org
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                self.step("Create new user by adding to an organization with roles {}".format(expected_roles))
                new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
                self._assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    def test_admin_adds_new_user_all_roles(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        org = self.test_org
        expected_roles = self.ALL_ROLES
        self.step("Create new user by adding to an organization with roles {}".format(expected_roles))
        new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    def test_org_manager_adds_new_user(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                org = self.test_org
                self.step("Org manager adds a new user to an organization with roles {}".format(expected_roles))
                new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles,
                                                                     inviting_client=inviting_client)
                self._assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    def test_non_manager_cannot_add_new_user_to_org(self):
        """DPNG-2271 /org/:org_guid/users returns different error messages for similar invalid requests"""
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(inviting_user_role=non_manager_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                self.step("Create new organization and add test user as {}".format(non_manager_roles))
                org = Organization.api_create()
                inviting_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_roles)
                self.step("Check that user cannot be added to organization by non-manager")
                org_users = User.api_get_list_via_organization(org.guid)
                self.assertRaisesUnexpectedResponse(403, "Forbidden", User.api_create_by_adding_to_organization,
                                                    org_guid=org.guid, roles=User.ORG_ROLES["auditor"],
                                                    inviting_client=inviting_client)
                # assert user list did not change
                self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    def test_cannot_add_user_with_non_email_username(self):
        """DPNG-2272 Attempt to add user with incorrect e-mail address results in Internal Server Error"""
        org = self.test_org
        self.step("Check that user with non valid username cannot be added to an organization")
        org_users = User.api_get_list_via_organization(org.guid)
        username = "non-valid-username{}".format(time.time())
        roles = self.ALL_ROLES
        self.assertRaisesUnexpectedResponse(409, "That email address is not valid",
                                            User.api_create_by_adding_to_organization, org_guid=org.guid,
                                            username=username, roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @unittest.expectedFailure
    def test_cannot_add_new_user_to_non_existing_org(self):
        """DPNG-2270 Using incorrect guid format in request results in Internal Server Error"""
        org_guid = "this-org-guid-is-not-correct"
        roles = self.ALL_ROLES
        self.step("Check that an error is raised when trying to add user using incorrect org guid")
        self.assertRaisesUnexpectedResponse(400, "???", User.api_create_by_adding_to_organization, org_guid=org_guid,
                                            roles=roles)

    def test_cannot_add_new_user_incorrect_role(self):
        org = self.test_org
        org_users = User.api_get_list_via_organization(org.guid)
        roles = ["i-don't-exist"]
        self.step("Check that error is raised when trying to add user using incorrect roles")
        self.assertRaisesUnexpectedResponse(400, "", User.api_create_by_adding_to_organization, org_guid=org.guid,
                                            roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)


class UpdateOrganizationUser(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs, User.cf_api_tear_down_test_users)
    def setUpClass(cls):
        cls.step("Create a test organization")
        cls.admin_org = Organization.api_create()
        cls.step("Onboard a test user")
        cls.test_user, cls.test_org = User.api_onboard()
        cls.test_client = cls.test_user.login()

    def test_update_org_user_add_new_role(self):
        updated_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        initial_roles = User.ORG_ROLES["manager"]
        expected_roles = initial_roles | User.ORG_ROLES["auditor"]
        self.step("Add test user to the organization with roles {}".format(initial_roles))
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        self.step("Update user roles to {}".format(expected_roles))
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=expected_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_update_org_user_remove_role(self):
        updated_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        initial_roles = self.ALL_ROLES
        expected_roles = initial_roles - User.ORG_ROLES["auditor"]
        self.step("Add test user to the organization with roles {}".format(initial_roles))
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        self.step("Update user roles to {}".format(expected_roles))
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=expected_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_update_org_user_change_role(self):
        updated_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        initial_roles = User.ORG_ROLES["auditor"]
        expected_roles = User.ORG_ROLES["billing_manager"]
        self.step("Add test user to the organization with roles {}".format(initial_roles))
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        self.step("Update user roles to {}".format(expected_roles))
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=expected_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_update_org_user_with_the_same_role(self):
        updated_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        initial_roles = expected_roles = User.ORG_ROLES["auditor"]
        self.step("Add test user to the organization with roles {}".format(initial_roles))
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        self.step("Update user roles to the same roles")
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=expected_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_cannot_remove_manager_role_for_the_only_org_manager(self):
        updated_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["manager"]
        new_roles = User.ORG_ROLES["auditor"]
        self.step("Add test user to the organization as the only manager")
        updated_user.api_add_to_organization(org_guid=org.guid, roles=expected_roles)
        self.step("Check that removing manager role of the only manager returns an error")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", updated_user.api_update_via_organization,
                                            org_guid=org.guid, new_roles=new_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    @unittest.expectedFailure
    def test_cannot_update_user_which_is_not_in_org(self):
        """DPNG-2196 It's possible to update user which was deleted from organization"""
        self.step("Add new user to the test organization")
        user_not_in_org = User.api_create_by_adding_to_organization(self.test_org.guid)
        self.step("Create another test organization")
        org = Organization.api_create()
        self.step("Check that attempt to update a user via org they are not in returns an error")
        org_users = User.api_get_list_via_organization(org.guid)
        self.assertRaisesUnexpectedResponse(400, "???", user_not_in_org.api_update_via_organization, org_guid=org.guid,
                                            new_roles=User.ORG_ROLES["auditor"])
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    def test_user_cannot_update_user_in_org_where_they_are_not_added(self):
        org = self.admin_org
        expected_roles = User.ORG_ROLES["auditor"]
        updating_client = self.test_client
        self.step("Add updating user to the organization as {}".format(expected_roles))
        self.test_user.api_add_to_organization(org_guid=org.guid, roles=expected_roles)
        self.step("Add updated user to the organization as {}".format(expected_roles))
        updated_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self.step("Check that non-admin user cannot update another user in the test organization")
        self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                            updated_user.api_update_via_organization, org_guid=org.guid,
                                            new_roles=User.ORG_ROLES["billing_manager"], client=updating_client)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_change_org_manager_role_in_org_with_two_managers(self):
        manager_roles = User.ORG_ROLES["manager"]
        new_roles = self.NON_MANAGER_ROLES
        org = self.test_org
        self.step("Add new manager to organization with a manager")
        updated_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=manager_roles)
        self.step("Check that it's possible to remove manager role from the user")
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=new_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, new_roles)

    @unittest.expectedFailure
    def test_cannot_update_non_existing_org_user(self):
        """DPNG-2270 Using incorrect guid format in request results in Internal Server Error"""
        org = self.test_org
        invalid_guid = "invalid-user-guid"
        roles = User.ORG_ROLES["billing_manager"]
        self.step("Check that updating user which is not in an organization returns an error")
        org_users = User.api_get_list_via_organization(org_guid=org.guid)
        self.assertRaisesUnexpectedResponse(400, "Bad Request", api.api_update_organization_user, org_guid=org.guid,
                                            user_guid=invalid_guid, new_roles=roles)
        self.assertListEqual(User.api_get_list_via_organization(org_guid=org.guid), org_users)

    @unittest.expectedFailure
    def test_cannot_update_org_user_in_non_existing_org(self):
        """DPNG-2270 Using incorrect guid format in request results in Internal Server Error"""
        invalid_guid = "invalid-org-guid"
        user_guid = self.test_user.guid
        roles = User.ORG_ROLES["billing_manager"]
        self.step("Check that updating user using invalid org guid returns an error")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", api.api_update_organization_user, org_guid=invalid_guid,
                                            user_guid=user_guid, new_roles=roles)

    def test_cannot_update_org_user_with_incorrect_role(self):
        updated_user = self.test_user
        initial_roles = User.ORG_ROLES["billing_manager"]
        invalid_roles = ["invalid role"]
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add test user to organization with roles {}".format(initial_roles))
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        self.step("Check that updating user using invalid role returns an error")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", updated_user.api_update_via_organization,
                                            org_guid=org.guid, new_roles=invalid_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, initial_roles)

    @unittest.expectedFailure
    def test_update_role_of_one_org_manager_cannot_update_second(self):
        """DPNG-2546 It's possible to update org role to non-manager for the last manager in an organization"""
        manager_role = User.ORG_ROLES["manager"]
        org = self.test_org
        self.step("Add two managers to the test organization")
        first_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=manager_role)
        second_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=manager_role)
        self.step("Remove manager role from one of the managers")
        first_user.api_update_via_organization(org_guid=org.guid, new_roles=self.NON_MANAGER_ROLES)
        self.step("Check that attempt to remove manager role from the second manager returns an error")
        self.assertRaisesUnexpectedResponse(400, "???", second_user.api_update_via_organization,
                                            org_guid=org.guid, new_roles=self.NON_MANAGER_ROLES)
        self._assert_user_in_org_and_roles(first_user, org.guid, self.NON_MANAGER_ROLES)
        self._assert_user_in_org_and_roles(second_user, org.guid, manager_role)


class DeleteOrganizationUser(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs, User.cf_api_tear_down_test_users)
    def setUpClass(cls):
        cls.step("Onboard test user")
        cls.test_user, cls.test_org = User.api_onboard()
        cls.test_client = cls.test_user.login()

    def test_admin_deletes_the_only_org_user_non_manager(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        for non_manager_role in self.NON_MANAGER_ROLES:
            non_manager_role = [non_manager_role]
            with self.subTest(roles=non_manager_role):
                self.step("Add user to organization with role {}".format(non_manager_role))
                deleted_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_role)
                self.step("Remove the user from the organization")
                deleted_user.api_delete_from_organization(org.guid)
                self._assert_user_not_in_org(deleted_user, org.guid)

    def test_admin_cannot_delete_the_only_org_manager(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        roles = User.ORG_ROLES["manager"]
        self.step("Add user to organization as manager")
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        self.step("Check that the only manager cannot be removed from the organization")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", deleted_user.api_delete_from_organization,
                                            org_guid=org.guid)
        self._assert_user_in_org_and_roles(deleted_user, org.guid, roles)

    def test_admin_deletes_one_of_org_users(self):
        not_deleted_user = self.test_user
        not_deleted_user_roles = User.ORG_ROLES["auditor"]
        deleted_user_roles = User.ORG_ROLES["billing_manager"]
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add two non-manager users to the organization")
        deleted_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=deleted_user_roles)
        not_deleted_user.api_add_to_organization(org_guid=org.guid, roles=not_deleted_user_roles)
        self.step("Remove one of the users from the organization")
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self._assert_user_in_org_and_roles(not_deleted_user, org.guid, not_deleted_user_roles)
        self._assert_user_not_in_org(deleted_user, org.guid)

    def test_admin_deletes_one_of_org_managers_cannot_delete_second(self):
        roles = User.ORG_ROLES["manager"]
        not_deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add two managers to the organization")
        not_deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        deleted_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=roles)
        self.step("Remove one of the managers from the organization")
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self._assert_user_not_in_org(deleted_user, org.guid)
        self.step("Check that removing the last org manager returns an error")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", not_deleted_user.api_delete_from_organization,
                                            org_guid=org.guid)
        self._assert_user_in_org_and_roles(not_deleted_user, org.guid, roles)

    def test_admin_updates_role_of_one_org_manager_cannot_delete_second(self):
        manager_role = User.ORG_ROLES["manager"]
        for updated_user_roles in self.NON_MANAGER_ROLES:
            updated_user_roles = [updated_user_roles]
            with self.subTest(updated_rols=updated_user_roles):
                manager_user = self.test_user
                self.step("Create a test organization")
                org = Organization.api_create()
                self.step("Add two managers to the organization")
                manager_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
                updated_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=manager_role)
                self.step("Update roles of one of the managers to {}".format(updated_user_roles))
                updated_user.api_update_via_organization(org_guid=org.guid, new_roles=updated_user_roles)
                self._assert_user_in_org_and_roles(updated_user, org.guid, updated_user_roles)
                self.step("Check that removing the last manger returns an error")
                self.assertRaisesUnexpectedResponse(400, "Bad Request", manager_user.api_delete_from_organization,
                                                    org_guid=org.guid)
                self._assert_user_in_org_and_roles(manager_user, org.guid, manager_role)

    def test_admin_cannot_delete_org_user_twice(self):
        """DPNG-2216 Deleting from org a user which is not in this org does not return any error"""
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=User.ORG_ROLES["auditor"])
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self.assertRaisesUnexpectedResponse(404, "", deleted_user.api_delete_from_organization, org_guid=org.guid)

    def test_admin_cannot_delete_non_existing_org_user(self):
        """DPNG-2216 Deleting from org a user which is not in this org does not return any error"""
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Check that an attempt to delete user which is not in org returns an error")
        self.assertRaisesUnexpectedResponse(404, "", deleted_user.api_delete_from_organization, org_guid=org.guid)

    def test_org_manager_can_delete_another_user(self):
        """DPNG-2459 Cannot delete user - 404"""
        for roles in User.ORG_ROLES.values():
            with self.subTest(deleted_user_roles=roles):
                org = self.test_org
                user_client = self.test_client
                self.step("Add user to the test org with roles {}".format(roles))
                deleted_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=roles)
                self.step("Org manager removes the user from the test org")
                deleted_user.api_delete_from_organization(org_guid=org.guid, client=user_client)
                self._assert_user_not_in_org(deleted_user, org.guid)

    def test_non_manager_cannot_delete_user(self):
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(non_manager_roles=non_manager_roles):
                deleted_user_roles = User.ORG_ROLES["auditor"]
                non_manager_user, non_manager_client = self.test_user, self.test_client
                self.step("Create a test organization")
                org = Organization.api_create()
                self.step("Add deleting user to the organization with roles {}".format(non_manager_roles))
                non_manager_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_roles)
                self.step("Add deleted user to the organization with roles {}".format(deleted_user_roles))
                deleted_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=deleted_user_roles)
                self.step("Check that non-manager cannot delete user from org")
                self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                    deleted_user.api_delete_from_organization, org_guid=org.guid,
                                                    client=non_manager_client)
                self._assert_user_in_org_and_roles(deleted_user, org.guid, deleted_user_roles)


class GetOrganizationUsers(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs, User.cf_api_tear_down_test_users)
    def setUpClass(cls):
        cls.step("Create a test organization")
        cls.test_org = Organization.api_create()
        cls.step("Add new manager user to the test org")
        cls.manager = User.api_create_by_adding_to_organization(org_guid=cls.test_org.guid, roles=User.ORG_ROLES["manager"])
        cls.manager_client = cls.manager.login()
        cls.step("Add non-manager users to the test org")
        cls.non_managers = {(roles,): User.api_create_by_adding_to_organization(org_guid=cls.test_org.guid, roles=[roles])
                            for roles in cls.NON_MANAGER_ROLES}
        cls.non_manager_clients = {roles: user.login() for roles, user in cls.non_managers.items()}

    def test_non_manager_in_org_cannot_get_org_users(self):
        for role, client in self.non_manager_clients.items():
            with self.subTest(user_role=role):
                self.step("Check that non-manager cannot get list of users in org")
                self.assertRaisesUnexpectedResponse(403, "Forbidden", User.api_get_list_via_organization,
                                                    org_guid=self.test_org.guid, client=client)

    def test_manager_can_get_org_users(self):
        self.step("Check that manager can get list of users in org")
        expected_users = [user for user in [self.manager] + list(self.non_managers.values())]
        user_list = User.api_get_list_via_organization(org_guid=self.test_org.guid, client=self.manager_client)
        self.assertUnorderedListEqual(user_list, expected_users)

    def test_user_not_in_org_cannot_get_org_users(self):
        self.step("Onboard new user, don't add them to the test org")
        user_not_in_org, _ = User.api_onboard()
        client = user_not_in_org.login()
        self.step("Check that the user cannot get list of users in the test org")
        self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                            User.api_get_list_via_organization, org_guid=self.test_org.guid,
                                            client=client)

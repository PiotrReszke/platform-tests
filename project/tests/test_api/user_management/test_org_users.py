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
        Organization.cf_api_tear_down_test_orgs()

    def _assert_user_in_org_and_roles(self, invited_user, org_guid, expected_roles):
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertInList(invited_user, org_users, "Invited user is not on org users list")
        invited_user_roles = list(invited_user.org_roles.get(org_guid, []))
        self.assertUnorderedListEqual(invited_user_roles, list(expected_roles),
                                      "User's roles in org: {}, expected {}".format(invited_user_roles,
                                                                                    list(expected_roles)))

    def _assert_user_not_in_org(self, user, org_guid):
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertNotInList(user, org_users, "User is among org users, although they shouldn't")


class AddExistingUserToOrganization(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.test_user, cls.test_org = User.api_onboard()
        cls.test_client = cls.test_user.login()

    def test_add_existing_user_with_no_roles(self):
        invited_user = self.test_user
        expected_roles = []
        org = Organization.api_create()
        invited_user.api_add_to_organization(org_guid=org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_existing_user_one_role(self):
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                invited_user = self.test_user
                org = Organization.api_create()
                invited_user.api_add_to_organization(org.guid, roles=expected_roles)
                self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_existing_user_all_roles(self):
        invited_user = self.test_user
        org = Organization.api_create()
        expected_roles = self.ALL_ROLES
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_user_which_is_already_in_org_with_the_same_role(self):
        invited_user = self.test_user
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["manager"]
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_user_which_is_already_in_org_with_different_role(self):
        invited_user = self.test_user
        org = Organization.api_create()
        roles_0 = User.ORG_ROLES["manager"]
        roles_1 = User.ORG_ROLES["auditor"]
        expected_roles = roles_0 | roles_1  # adding user with a new role results in the user having sum of the roles
        invited_user.api_add_to_organization(org.guid, roles=roles_0)
        invited_user.api_add_to_organization(org.guid, roles=roles_1)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_org_manager_adds_existing_user(self):
        invited_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                org = Organization.api_create()
                inviting_user.api_add_to_organization(org.guid, roles=User.ORG_ROLES["manager"])
                invited_user.api_add_to_organization(org.guid, roles=expected_roles, client=inviting_client)
                self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @unittest.expectedFailure
    def test_non_manager_cannot_add_existing_user_to_org(self):
        """DPNG-2271 /org/:org_guid/users returns different error messages for similar invalid requests"""
        invited_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(inviting_user_role=non_manager_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                org = Organization.api_create()
                inviting_user.api_add_to_organization(org.guid, roles=non_manager_roles)
                expected_roles = User.ORG_ROLES["auditor"]
                self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                    invited_user.api_add_to_organization, org_guid=org.guid,
                                                    roles=expected_roles, client=inviting_client)
                self._assert_user_not_in_org(invited_user, org.guid)

    def test_user_cannot_add_themselves_to_org(self):
        invited_user, inviting_client = self.test_user, self.test_client
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["auditor"]
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
        self.assertRaisesUnexpectedResponse(400, "Bad Request", invited_user.api_add_to_organization,
                                            org_guid=invalid_org_guid, roles=roles)

    def test_cannot_add_existing_user_with_incorrect_role(self):
        invited_user = self.test_user
        org = Organization.api_create()
        invalid_role = ["incorrect-role"]
        self.assertRaisesUnexpectedResponse(400, "Bad Request", invited_user.api_add_to_organization, org_guid=org.guid,
                                            roles=invalid_role)
        self._assert_user_not_in_org(invited_user, org.guid)


class AddNewUserToOrganization(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.test_user, cls.test_org = User.api_onboard()
        cls.test_client = cls.test_user.login()

    @unittest.expectedFailure
    def test_add_new_user_with_no_roles(self):
        """DPNG-2540 Cannot add new user to organization without roles"""
        org = self.test_org
        expected_roles = []
        invited_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    def test_admin_adds_new_user_one_role(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        org = self.test_org
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
                self._assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    def test_admin_adds_new_user_all_roles(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        org = self.test_org
        expected_roles = self.ALL_ROLES
        new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self._assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    def test_org_manager_adds_new_user(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                org = self.test_org
                new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles,
                                                                     inviting_client=inviting_client)
                self._assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    @unittest.expectedFailure
    def test_non_manager_cannot_add_new_user_to_org(self):
        """DPNG-2271 /org/:org_guid/users returns different error messages for similar invalid requests"""
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(inviting_user_role=non_manager_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                org = Organization.api_create()
                inviting_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_roles)
                org_users = User.api_get_list_via_organization(org.guid)
                self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                    User.api_create_by_adding_to_organization, org_guid=org.guid,
                                                    roles=User.ORG_ROLES["auditor"], inviting_client=inviting_client)
                # assert user list did not change
                self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    def test_cannot_add_user_with_non_email_username(self):
        """DPNG-2272 Attempt to add user with incorrect e-mail address results in Internal Server Error"""
        org = self.test_org
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
        self.assertRaisesUnexpectedResponse(400, "???", User.api_create_by_adding_to_organization, org_guid=org_guid,
                                            roles=roles)

    def test_cannot_add_new_user_incorrect_role(self):
        org = self.test_org
        org_users = User.api_get_list_via_organization(org.guid)
        roles = ["i-don't-exist"]
        self.assertRaisesUnexpectedResponse(400, "", User.api_create_by_adding_to_organization, org_guid=org.guid,
                                            roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)


class UpdateOrganizationUser(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.admin_org = Organization.api_create()
        cls.test_user, cls.test_org = User.api_onboard()
        cls.test_client = cls.test_user.login()

    def test_update_org_user_add_new_role(self):
        updated_user = self.test_user
        org = Organization.api_create()
        initial_roles = User.ORG_ROLES["manager"]
        expected_roles = initial_roles | User.ORG_ROLES["auditor"]
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=expected_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_update_org_user_remove_role(self):
        updated_user = self.test_user
        org = Organization.api_create()
        initial_roles = self.ALL_ROLES
        expected_roles = initial_roles - User.ORG_ROLES["auditor"]
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=expected_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_update_org_user_change_role(self):
        updated_user = self.test_user
        org = Organization.api_create()
        initial_roles = User.ORG_ROLES["auditor"]
        expected_roles = User.ORG_ROLES["billing_manager"]
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=expected_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_update_org_user_with_the_same_role(self):
        updated_user = self.test_user
        org = Organization.api_create()
        initial_roles = expected_roles = User.ORG_ROLES["auditor"]
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=expected_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_cannot_remove_manager_role_for_the_only_org_manager(self):
        updated_user = self.test_user
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["manager"]
        new_roles = User.ORG_ROLES["auditor"]
        updated_user.api_add_to_organization(org_guid=org.guid, roles=expected_roles)
        self.assertRaisesUnexpectedResponse(400, "Bad Request", updated_user.api_update_via_organization,
                                            org_guid=org.guid, new_roles=new_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    @unittest.expectedFailure
    def test_cannot_update_user_which_is_not_in_org(self):
        """DPNG-2196 It's possible to update user which was deleted from organization"""
        user_not_in_org = User.api_create_by_adding_to_organization(self.test_org.guid)
        org = Organization.api_create()
        org_users = User.api_get_list_via_organization(org.guid)
        self.assertRaisesUnexpectedResponse(400, "???", user_not_in_org.api_update_via_organization, org_guid=org.guid,
                                            new_roles=User.ORG_ROLES["auditor"])
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @unittest.expectedFailure
    def test_user_cannot_update_themselves_in_org_where_they_are_not_added(self):
        """DPNG-2271 /org/:org_guid/users returns different error messages for similar invalid requests"""
        for roles in User.ORG_ROLES.values():
            with self.subTest(new_roles=roles):
                updated_user, updating_client = self.test_user, self.test_client
                org = Organization.api_create()
                initial_roles = self.ALL_ROLES
                new_roles = roles
                updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
                self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                    updated_user.api_update_via_organization, org_guid=org.guid,
                                                    new_roles=new_roles, client=updating_client)
                self._assert_user_in_org_and_roles(updated_user, org.guid, initial_roles)

    def test_user_cannot_update_user_in_org_where_they_are_not_added(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        org = self.admin_org
        expected_roles = User.ORG_ROLES["auditor"]
        updated_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        updating_client = self.test_client
        self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                            updated_user.api_delete_from_organization, org_guid=org.guid,
                                            client=updating_client)
        self._assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    def test_change_org_manager_role_in_org_with_two_managers(self):
        manager_roles = User.ORG_ROLES["manager"]
        new_roles = self.NON_MANAGER_ROLES
        org = self.test_org
        updated_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=manager_roles)
        manager = self.test_user
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=new_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, new_roles)

    @unittest.expectedFailure
    def test_cannot_update_non_existing_org_user(self):
        """DPNG-2270 Using incorrect guid format in request results in Internal Server Error"""
        org = self.test_org
        org_users = User.api_get_list_via_organization(org_guid=org.guid)
        invalid_guid = "invalid-user-guid"
        roles = User.ORG_ROLES["billing_manager"]
        self.assertRaisesUnexpectedResponse(400, "Bad Request", api.api_update_organization_user, org_guid=org.guid,
                                            user_guid=invalid_guid, new_roles=roles)
        self.assertListEqual(User.api_get_list_via_organization(org_guid=org.guid), org_users)

    @unittest.expectedFailure
    def test_cannot_update_org_user_in_non_existing_org(self):
        """DPNG-2270 Using incorrect guid format in request results in Internal Server Error"""
        invalid_guid = "invalid-org-guid"
        user_guid = self.test_user.guid
        roles = User.ORG_ROLES["billing_manager"]
        self.assertRaisesUnexpectedResponse(400, "Bad Request", api.api_update_organization_user, org_guid=invalid_guid,
                                            user_guid=user_guid, new_roles=roles)

    def test_cannot_update_org_user_with_incorrect_role(self):
        org = Organization.api_create()
        updated_user = self.test_user
        initial_roles = User.ORG_ROLES["billing_manager"]
        invalid_roles = ["invalid role"]
        updated_user.api_add_to_organization(org_guid=org.guid, roles=initial_roles)
        self.assertRaisesUnexpectedResponse(400, "", updated_user.api_update_via_organization, org_guid=org.guid,
                                            new_roles=invalid_roles)
        self._assert_user_in_org_and_roles(updated_user, org.guid, initial_roles)

    @unittest.expectedFailure
    def test_update_role_of_one_org_manager_cannot_update_second(self):
        """DPNG-2546 It's possible to update org role to non-manager for the last manager in an organization"""
        manager_role = User.ORG_ROLES["manager"]
        manager_user = self.test_user
        updated_user = User.api_create_by_adding_to_organization(org_guid=self.test_org.guid)
        org = self.test_org
        manager_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
        updated_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
        updated_user.api_update_via_organization(org_guid=org.guid, new_roles=self.NON_MANAGER_ROLES)
        self.assertRaisesUnexpectedResponse(400, "???", manager_user.api_update_via_organization,
                                            org_guid=org.guid, new_roles=self.NON_MANAGER_ROLES)
        self._assert_user_in_org_and_roles(updated_user, org.guid, self.NON_MANAGER_ROLES)
        self._assert_user_in_org_and_roles(manager_user, org.guid, manager_role)


class DeleteOrganizationUser(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.test_user, cls.test_org = User.api_onboard()
        cls.test_client = cls.test_user.login()

    def test_admin_deletes_the_only_org_user_non_manager(self):
        deleted_user = self.test_user
        org = Organization.api_create()
        for non_manager_role in self.NON_MANAGER_ROLES:
            non_manager_role = [non_manager_role]
            with self.subTest(roles=non_manager_role):
                deleted_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_role)
                deleted_user.api_delete_from_organization(org.guid)
                self._assert_user_not_in_org(deleted_user, org.guid)

    def test_admin_cannot_delete_the_only_org_manager(self):
        deleted_user = self.test_user
        org = Organization.api_create()
        roles = User.ORG_ROLES["manager"]
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        self.assertRaisesUnexpectedResponse(400, "Bad Request", deleted_user.api_delete_from_organization, org_guid=org.guid)
        self._assert_user_in_org_and_roles(deleted_user, org.guid, roles)

    def test_admin_deletes_one_of_org_users(self):
        not_deleted_user = self.test_user
        not_deleted_user_roles = User.ORG_ROLES["auditor"]
        deleted_user = User.api_create_by_adding_to_organization(org_guid=self.test_org.guid)
        deleted_user_roles = User.ORG_ROLES["billing_manager"]
        org = Organization.api_create()
        not_deleted_user.api_add_to_organization(org_guid=org.guid, roles=not_deleted_user_roles)
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=deleted_user_roles)
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self._assert_user_in_org_and_roles(not_deleted_user, org.guid, not_deleted_user_roles)
        self._assert_user_not_in_org(deleted_user, org.guid)

    def test_admin_deletes_one_of_org_managers_cannot_delete_second(self):
        roles = User.ORG_ROLES["manager"]
        not_deleted_user = self.test_user
        deleted_user = User.api_create_by_adding_to_organization(org_guid=self.test_org.guid)
        org = Organization.api_create()
        not_deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self._assert_user_not_in_org(deleted_user, org.guid)
        self.assertRaisesUnexpectedResponse(400, "", not_deleted_user.api_delete_from_organization, org_guid=org.guid)
        self._assert_user_in_org_and_roles(not_deleted_user, org.guid, roles)

    def test_admin_updates_role_of_one_org_manager_cannot_delete_second(self):
        manager_role = User.ORG_ROLES["manager"]
        for updated_user_roles in self.NON_MANAGER_ROLES:
            updated_user_roles = [updated_user_roles]
            with self.subTest(updated_rols=updated_user_roles):
                manager_user = self.test_user
                updated_user = User.api_create_by_adding_to_organization(org_guid=self.test_org.guid)
                org = Organization.api_create()
                manager_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
                updated_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
                updated_user.api_update_via_organization(org_guid=org.guid, new_roles=updated_user_roles)
                self.assertRaisesUnexpectedResponse(400, "", manager_user.api_delete_from_organization,
                                                    org_guid=org.guid)
                self._assert_user_in_org_and_roles(manager_user, org.guid, manager_role)
                self._assert_user_in_org_and_roles(updated_user, org.guid, updated_user_roles)

    @unittest.expectedFailure
    def test_admin_cannot_delete_org_user_twice(self):
        """DPNG-2216 Deleting from org a user which is not in this org does not return any error"""
        deleted_user = self.test_user
        org = Organization.api_create()
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=User.ORG_ROLES["auditor"])
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self.assertRaisesUnexpectedResponse(404, "???", deleted_user.api_delete_from_organization, org_guid=org.guid)

    @unittest.expectedFailure
    def test_admin_cannot_delete_non_existing_org_user(self):
        """DPNG-2216 Deleting from org a user which is not in this org does not return any error"""
        deleted_user = self.test_user
        org = Organization.api_create()
        self.assertRaisesUnexpectedResponse(404, "???", deleted_user.api_delete_from_organization, org_guid=org.guid)

    @unittest.expectedFailure
    def test_org_manager_can_delete_another_user(self):
        """DPNG-2459 Cannot delete user - 404"""
        for roles in User.ORG_ROLES.values():
            with self.subTest(deleted_user_roles=roles):
                org = self.test_org
                user_client = self.test_client
                deleted_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=roles)
                deleted_user.api_delete_from_organization(org_guid=org.guid, client=user_client)
                self._assert_user_not_in_org(deleted_user, org.guid)

    def test_non_manager_cannot_delete_user(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(non_manager_roles=non_manager_roles):
                org = Organization.api_create()
                non_manager_user, non_manager_client = self.test_user, self.test_client
                non_manager_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_roles)
                deleted_user_roles = User.ORG_ROLES["auditor"]
                deleted_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=deleted_user_roles)
                self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                    deleted_user.api_delete_from_organization, org_guid=org.guid,
                                                    client=non_manager_client)
                self._assert_user_in_org_and_roles(deleted_user, org.guid, deleted_user_roles)

    def test_user_cannot_delete_user_from_org_they_are_not_added(self):
        """DPNG-2181 Cannot add new organization user with role other than manager"""
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["auditor"]
        deleted_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        user_client = self.test_client
        self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                            deleted_user.api_delete_from_organization, org_guid=org.guid,
                                            client=user_client)
        self._assert_user_in_org_and_roles(deleted_user, org.guid, expected_roles)


class GetOrganizationUsers(BaseOrgUserClass):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.test_org = Organization.api_create()
        cls.test_users = {tuple(roles): User.api_create_by_adding_to_organization(org_guid=cls.test_org.guid,
                                                                                  roles=roles)
                          for roles in User.ORG_ROLES.values()}
        cls.test_clients = {roles: user.login() for roles, user in cls.test_users.items()}

    @unittest.expectedFailure
    def test_user_in_org_can_get_org_users(self):
        """DPNG-2460 Non-manager, non-admin user cannot access User Management"""
        expected_org_users = User.api_get_list_via_organization(org_guid=self.test_org.guid)
        for role, client in self.test_clients.items():
            with self.subTest(user_role=role):
                org_users = User.api_get_list_via_organization(org_guid=self.test_org.guid, client=client)
                self.assertListEqual(org_users, expected_org_users)

    def test_user_not_in_org_cannot_get_org_users(self):
        user_not_in_org, _ = User.api_onboard()
        client = user_not_in_org.login()
        self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                            User.api_get_list_via_organization, org_guid=self.test_org.guid,
                                            client=client)


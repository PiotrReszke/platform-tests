#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import time
import itertools

from constants.tap_components import TapComponent as TAP
from test_utils import ApiTestCase, get_logger, platform_api_calls as api, cleanup_after_failed_setup, priority
from test_utils import components
from objects import Organization, User
from constants.HttpStatus import UserManagementHttpStatus as HttpStatus

logger = get_logger("test org users")

USERS = []
TEST_ORG = None


def tearDownModule():
    User.cf_api_tear_down_test_users()
    User.api_tear_down_test_invitations()
    Organization.cf_api_tear_down_test_orgs()


@cleanup_after_failed_setup(tearDownModule)
def setUpModule():
    global USERS, TEST_ORG
    logger.debug("Create users for org tests")
    users, org = User.api_create_users_for_tests(4)
    TEST_ORG = org
    for user in users:
        client = user.login()
        USERS.append({"user": user, "client": client})


class BaseOrgUserClass(ApiTestCase):
    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]

    @classmethod
    def tearDownClass(cls):
        # silence tearDownClass method inherited from ApiTestCase class, so users are not deleted before tearDownModule
        pass

    def _assert_user_not_in_org(self, user, org_guid):
        self.step("Check that the user is not in the organization.")
        org_users = User.api_get_list_via_organization(org_guid)
        self.assertNotIn(user, org_users, "User is among org users, although they shouldn't")


@components(TAP.user_management, TAP.auth_gateway)
class AddExistingUserToOrganization(BaseOrgUserClass):
    @classmethod
    def setUpClass(cls):
        cls.test_user = USERS[0]["user"]
        cls.test_client = USERS[0]["client"]

    @priority.medium
    def test_add_existing_user_with_no_roles(self):
        invited_user = self.test_user
        expected_roles = []
        self.step("Create an organization.")
        org = Organization.api_create()
        self.step("Add a platform user to organization with no roles.")
        invited_user.api_add_to_organization(org_guid=org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.high
    def test_admin_adds_existing_user_one_role(self):
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                invited_user = self.test_user
                self.step("Create an organization.")
                org = Organization.api_create()
                self.step("Add a platform user to organization with roles {}.".format(expected_roles))
                invited_user.api_add_to_organization(org.guid, roles=expected_roles)
                self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.low
    def test_admin_adds_existing_user_all_roles(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = self.ALL_ROLES
        self.step("Add a platform user to organization with roles {}.".format(expected_roles))
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.low
    def test_admin_adds_user_which_is_already_in_org_with_the_same_role(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["manager"]
        self.step("Add a platform user to organization with roles {}.".format(expected_roles))
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self.step("Add the same user to the same organization with the same roles")
        invited_user.api_add_to_organization(org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.low
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
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.medium
    def test_org_manager_adds_existing_user(self):
        invited_user = USERS[1]["user"]
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                self.step("Create an organization.")
                org = Organization.api_create()
                self.step("Add a platform user as manager to the organization.")
                inviting_user.api_add_to_organization(org.guid, roles=User.ORG_ROLES["manager"])
                self.step("The new manager adds a platform user to the organization.")
                invited_user.api_add_to_organization(org.guid, roles=expected_roles, client=inviting_client)
                self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.medium
    def test_non_manager_cannot_add_existing_user_to_org(self):
        invited_user = USERS[1]["user"]
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
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    invited_user.api_add_to_organization, org_guid=org.guid,
                                                    roles=expected_roles, client=inviting_client)
                self._assert_user_not_in_org(invited_user, org.guid)

    @priority.medium
    def test_user_cannot_add_themselves_to_org(self):
        invited_user, inviting_client = self.test_user, self.test_client
        self.step("Create an organization.")
        org = Organization.api_create()
        expected_roles = User.ORG_ROLES["auditor"]
        self.step("Check that a platform user is not able to add themselves to the organization")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            invited_user.api_add_to_organization, org_guid=org.guid,
                                            roles=expected_roles, client=inviting_client)
        self._assert_user_not_in_org(invited_user, org.guid)

    @priority.low
    def test_cannot_add_existing_user_to_non_existing_org(self):
        invited_user = self.test_user
        invalid_org_guid = "this-org-guid-is-not-correct"
        roles = self.ALL_ROLES
        self.step("Check that adding user to organization using invalid org guid raises an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            invited_user.api_add_to_organization, org_guid=invalid_org_guid,
                                            roles=roles)

    @priority.low
    def test_cannot_add_existing_user_with_incorrect_role(self):
        invited_user = self.test_user
        self.step("Create an organization.")
        org = Organization.api_create()
        invalid_role = ["incorrect-role"]
        self.step("Check that it is not possible to add user to the organization with role {}".format(invalid_role))
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            invited_user.api_add_to_organization, org_guid=org.guid, roles=invalid_role)
        self._assert_user_not_in_org(invited_user, org.guid)


@components(TAP.user_management, TAP.auth_gateway)
class AddNewUserToOrganization(BaseOrgUserClass):
    @classmethod
    def setUpClass(cls):
        cls.test_user = USERS[0]["user"]
        cls.test_client = USERS[0]["client"]
        cls.test_org = TEST_ORG

    @priority.medium
    def test_add_new_user_with_no_roles(self):
        org = self.test_org
        expected_roles = []
        self.step("Create new user by adding to an organization with no roles")
        invited_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(invited_user, org.guid, expected_roles)

    @priority.high
    def test_admin_adds_new_user_one_role(self):
        org = self.test_org
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                self.step("Create new user by adding to an organization with roles {}".format(expected_roles))
                new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
                self.assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    @priority.low
    def test_admin_adds_new_user_all_roles(self):
        org = self.test_org
        expected_roles = self.ALL_ROLES
        self.step("Create new user by adding to an organization with roles {}".format(expected_roles))
        new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles)
        self.assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    @priority.medium
    def test_org_manager_adds_new_user(self):
        for expected_roles in User.ORG_ROLES.values():
            with self.subTest(role=expected_roles):
                inviting_client = self.test_client
                org = self.test_org
                self.step("Org manager adds a new user to an organization with roles {}".format(expected_roles))
                new_user = User.api_create_by_adding_to_organization(org_guid=org.guid, roles=expected_roles,
                                                                     inviting_client=inviting_client)
                self.assert_user_in_org_and_roles(new_user, org.guid, expected_roles)

    @priority.medium
    def test_non_manager_cannot_add_new_user_to_org(self):
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(inviting_user_role=non_manager_roles):
                inviting_user, inviting_client = self.test_user, self.test_client
                self.step("Create new organization and add test user as {}".format(non_manager_roles))
                org = Organization.api_create()
                inviting_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_roles)
                self.step("Check that user cannot be added to organization by non-manager")
                org_users = User.api_get_list_via_organization(org.guid)
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    User.api_create_by_adding_to_organization, org_guid=org.guid,
                                                    roles=User.ORG_ROLES["auditor"], inviting_client=inviting_client)
                # assert user list did not change
                self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @priority.low
    def test_cannot_add_user_with_non_email_username(self):
        org = self.test_org
        self.step("Check that user with non valid username cannot be added to an organization")
        org_users = User.api_get_list_via_organization(org.guid)
        username = "non-valid-username{}".format(time.time())
        roles = self.ALL_ROLES
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMAIL_ADDRESS_NOT_VALID,
                                            User.api_create_by_adding_to_organization, org_guid=org.guid,
                                            username=username, roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @priority.low
    def test_cannot_add_new_user_to_non_existing_org(self):
        org_guid = "this-org-guid-is-not-correct"
        roles = self.ALL_ROLES
        self.step("Check that an error is raised when trying to add user using incorrect org guid")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            User.api_create_by_adding_to_organization, org_guid=org_guid, roles=roles)

    @priority.low
    def test_cannot_add_new_user_incorrect_role(self):
        org = self.test_org
        org_users = User.api_get_list_via_organization(org.guid)
        roles = ["i-don't-exist"]
        self.step("Check that error is raised when trying to add user using incorrect roles")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_EMPTY,
                                            User.api_create_by_adding_to_organization, org_guid=org.guid, roles=roles)
        # assert user list did not change
        self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)


@components(TAP.user_management)
class UpdateOrganizationUser(BaseOrgUserClass):
    client_permission = {
        "admin": True,
        "manager": True,
        "auditor": False,
        "billing_manager": False
    }

    @classmethod
    def setUpClass(cls):
        cls.user = USERS[0]["user"]
        cls.user_client = USERS[0]["client"]
        cls.test_user = USERS[1]["user"]
        cls.non_manager_roles = [(name, user_role) for name, user_role in User.ORG_ROLES.items()
                                 if name is not "manager"]

    def _get_client(self, client_name):
        if client_name == "admin":
            return None
        return self.user_client

    def _add_test_user_to_org(self, user, org, roles):
        self.step("Add user with {} role(s)".format(roles))
        user.api_add_to_organization(org.guid, roles=roles)
        return user

    def _create_org_and_init_users(self, tested_client_type, test_user_initial_roles=None):
        """
        Method creates organization and adds two users to it (if all parameters are provided).
        :param tested_client_type: Type of user and client to create (admin, manager, billing_manager, auditor)
        :param test_user_initial_roles: Initial roles for the user on which we want perform update tests
        :return: org - created organization, testing_user - the user which will be used to update other users ,
        user_client - client of testing_user, test_user - the user which will be updated in tests
        """
        self.step("Create test org")
        org = Organization.api_create()
        testing_user = test_user = None
        user_client = self._get_client(tested_client_type)
        if user_client:
            testing_user = self._add_test_user_to_org(self.user, org, User.ORG_ROLES[tested_client_type])
        if test_user_initial_roles is not None:
            test_user = self._add_test_user_to_org(self.test_user, org, test_user_initial_roles)
        return org, testing_user, user_client, test_user

    def _update_roles_with_client(self, client_name, init_roles, updated_roles, is_authorized, msg):
        org, _, client, updated_user = self._create_org_and_init_users(client_name, init_roles)
        self.step(msg)
        with self.subTest(user_type=client_name, new_role=updated_roles):
            if is_authorized:
                updated_user.api_update_org_roles(org.guid, new_roles=updated_roles, client=client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, updated_roles)
            else:
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    updated_user.api_update_org_roles, org.guid,
                                                    new_roles=updated_roles, client=client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, init_roles)

    @priority.high
    def test_update_org_user_add_new_role(self):
        permissions, roles = self.client_permission.items(), User.ORG_ROLES.values()
        for (client_name, is_authorized), new_role in itertools.product(permissions, roles):
            self._update_roles_with_client(client_name, {}, new_role, is_authorized,
                                           "As {} try to add new role {} to user".format(client_name, new_role))

    @priority.medium
    def test_update_org_user_remove_role(self):
        permissions, roles = self.client_permission.items(), self.NON_MANAGER_ROLES
        for (client_name, is_authorized), role in itertools.product(permissions, roles):
            self._update_roles_with_client(client_name, self.ALL_ROLES, self.ALL_ROLES - {role}, is_authorized,
                                           "As {} try to remove user role {}".format(client_name, {role}))

    @priority.medium
    def test_update_org_user_change_role(self):
        initial_roles = User.ORG_ROLES["auditor"]
        expected_roles = User.ORG_ROLES["billing_manager"]
        for client_name, is_authorized in self.client_permission.items():
            self._update_roles_with_client(client_name, initial_roles, expected_roles, is_authorized,
                                           "As {} try to change user roles".format(client_name))

    @priority.low
    def test_update_org_user_with_the_same_role(self):
        permissions, roles = self.client_permission.items(), User.ORG_ROLES.values()
        for (client_name, is_authorized), role in itertools.product(permissions, roles):
            self._update_roles_with_client(client_name, role, role, is_authorized,
                                           "As {} update user with same role".format(client_name))

    @priority.low
    def test_cannot_remove_manager_role_for_the_only_org_manager(self):
        expected_roles = self.ALL_ROLES
        org, _, client, updated_user = self._create_org_and_init_users("admin", expected_roles)
        self.step("Check that removing manager role of the only org manager as admin, returns an error")
        new_roles = expected_roles - User.SPACE_ROLES["manager"]
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            updated_user.api_update_org_roles, org_guid=org.guid,
                                            new_roles=new_roles, client=client)
        self.assert_user_in_org_and_roles(updated_user, org.guid, expected_roles)

    @priority.low
    def test_user_cannot_update_user_in_org_where_they_are_not_added(self):
        initial_role = User.ORG_ROLES["billing_manager"]
        role = User.ORG_ROLES["auditor"]
        self.step("Create test organization")
        org = Organization.api_create()
        self.step("Add test user to org")
        updated_user = self.test_user
        updated_user.api_add_to_organization(org.guid, roles=initial_role)
        self.step("Test that users cannot change roles of users from another org")
        for user_role in User.ORG_ROLES.values():
            other_org = Organization.api_create()
            self.user.api_add_to_organization(other_org.guid, roles=user_role)
            with self.subTest(user_type=user_role):
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    updated_user.api_update_org_roles, org.guid, new_roles=role,
                                                    client=self.user_client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, initial_role)

    @priority.low
    def test_cannot_update_user_which_is_not_in_org(self):
        user_not_in_org = USERS[1]["user"]
        self.step("Create test organization")
        org = Organization.api_create()
        self.step("Check that attempt to update a user via org they are not in returns an error")
        org_users = User.api_get_list_via_organization(org.guid)
        self.step("Get only clients that are authorized to update other users roles")
        tested_clients = [client_name for client_name, is_authorized in self.client_permission.items() if is_authorized]
        for client_name in tested_clients:
            with self.subTest(client_type=client_name):
                client = self._get_client(client_name)
                if client_name == "admin":
                    self.assertRaisesUnexpectedResponse(
                        HttpStatus.CODE_NOT_FOUND,
                        HttpStatus.MSG_USER_NOT_EXIST_IN_ORGANIZATION.format(user_not_in_org.guid, org.guid),
                        user_not_in_org.api_update_org_roles, org_guid=org.guid, new_roles=User.ORG_ROLES["auditor"],
                        client=client)
                else:
                    self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                        user_not_in_org.api_update_org_roles, org_guid=org.guid,
                                                        new_roles=User.ORG_ROLES["auditor"], client=client)
                self.assertListEqual(User.api_get_list_via_organization(org.guid), org_users)

    @priority.low
    def test_change_org_manager_role_in_org_with_two_managers(self):
        manager_roles = User.ORG_ROLES["manager"]
        new_roles = self.NON_MANAGER_ROLES
        org, _, _, updated_user = self._create_org_and_init_users("manager", manager_roles)
        self.step("Check that it's possible to remove manager role from the user")
        updated_user.api_update_org_roles(org_guid=org.guid, new_roles=new_roles)
        self.assert_user_in_org_and_roles(updated_user, org.guid, new_roles)

    @priority.low
    def test_cannot_update_non_existing_org_user(self):
        org = TEST_ORG
        invalid_guid = "invalid-user-guid"
        roles = User.ORG_ROLES["billing_manager"]
        self.step("Check that updating user which is not in an organization returns an error")
        org_users = User.api_get_list_via_organization(org_guid=org.guid)
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            api.api_update_org_user_roles, org_guid=org.guid, user_guid=invalid_guid,
                                            new_roles=roles)
        self.assertListEqual(User.api_get_list_via_organization(org_guid=org.guid), org_users)

    @priority.low
    def test_cannot_update_org_user_in_non_existing_org(self):
        invalid_guid = "invalid-org-guid"
        user_guid = self.test_user.guid
        roles = User.ORG_ROLES["billing_manager"]
        self.step("Check that updating user using invalid org guid returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_WRONG_UUID_FORMAT_EXCEPTION,
                                            api.api_update_org_user_roles, org_guid=invalid_guid, user_guid=user_guid,
                                            new_roles=roles)

    @priority.low
    def test_cannot_update_org_user_with_incorrect_role(self):
        initial_roles = User.ORG_ROLES["billing_manager"]
        invalid_roles = ["invalid role"]
        for client_name, _ in self.non_manager_roles:
            org, _, _, updated_user = self._create_org_and_init_users(client_name, initial_roles)
            self.step("Check that updating user using invalid role returns an error")
            self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                                updated_user.api_update_org_roles, org_guid=org.guid,
                                                new_roles=invalid_roles)
            self.assert_user_in_org_and_roles(updated_user, org.guid, initial_roles)

    @priority.low
    def test_update_role_of_one_org_manager_cannot_update_second(self):
        manager_role = User.ORG_ROLES["manager"]
        org, first_user, _, second_user = self._create_org_and_init_users("manager", manager_role)
        self.step("Remove manager role from one of the managers")
        first_user.api_update_org_roles(org_guid=org.guid, new_roles=self.NON_MANAGER_ROLES)
        self.step("Check that attempt to remove manager role from the second manager returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            second_user.api_update_org_roles, org_guid=org.guid,
                                            new_roles=self.NON_MANAGER_ROLES)
        self.assert_user_in_org_and_roles(first_user, org.guid, self.NON_MANAGER_ROLES)
        self.assert_user_in_org_and_roles(second_user, org.guid, manager_role)

    @priority.low
    def test_non_manager_users_cannot_change_their_roles(self):
        self.step("Test non org managers cannot change their roles")
        for client_name, user_role in self.non_manager_roles:
            org, updated_user, client, _ = self._create_org_and_init_users(client_name)
            new_roles = self.NON_MANAGER_ROLES - user_role
            self.step("Try to change role as '{}'".format(client_name))
            with self.subTest(user_type=user_role):
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    updated_user.api_update_org_roles, org.guid, new_roles=new_roles,
                                                    client=client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, user_role)

    @priority.low
    def test_non_manager_users_cannot_change_their_roles_to_org_manager(self):
        for client_name, user_role in self.non_manager_roles:
            org, updated_user, client, _ = self._create_org_and_init_users(client_name)
            self.step("Try to change role as '{}'".format(client_name))
            with self.subTest(user_type=user_role):
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    updated_user.api_update_org_roles, org.guid,
                                                    new_roles=User.ORG_ROLES["manager"], client=client)
                self.assert_user_in_org_and_roles(updated_user, org.guid, user_role)

    @priority.low
    def test_org_manager_cannot_delete_own_role_while_being_the_only_org_manager(self):
        manager_role = User.ORG_ROLES["manager"]
        org, updated_user, client, _ = self._create_org_and_init_users("manager")
        self.step("As org manager try to delete self 'org manager' role")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            updated_user.api_update_org_roles, org.guid, new_roles={}, client=client)
        self.assert_user_in_org_and_roles(updated_user, org.guid, manager_role)

    @priority.low
    def test_org_manager_removes_own_role_when_there_is_another_org_manager(self):
        manager_role = User.ORG_ROLES["manager"]
        org, updated_user, client, _ = self._create_org_and_init_users("manager", manager_role)
        self.step("As one of the org managers delete own 'org manager' role")
        updated_user.api_update_org_roles(org.guid, new_roles={}, client=client)
        self.assert_user_in_org_and_roles(updated_user, org.guid, {})

    @priority.medium
    def test_org_manager_add_roles_to_self(self):
        expected_role = User.ORG_ROLES["manager"]
        org, updated_user, client, _ = self._create_org_and_init_users("manager")
        self.step("As org manager add to yourself new roles")
        for _, user_role in self.non_manager_roles:
            expected_role = expected_role | user_role
            updated_user.api_update_org_roles(org.guid, new_roles=expected_role, client=client)
            self.assert_user_in_org_and_roles(updated_user, org.guid, expected_role)

    @priority.low
    def test_send_org_role_update_request_with_empty_body(self):
        expected_roles = User.ORG_ROLES["manager"]
        self.step("Create new platform user by adding to org")
        test_user = User.api_create_by_adding_to_organization(org_guid=TEST_ORG.guid, roles=expected_roles)
        self.step("Send request with empty body")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_CONFLICT, HttpStatus.MSG_CANNOT_PERFORM_REQ_WITHOUT_ROLES,
                                            api.api_update_org_user_roles, TEST_ORG.guid, test_user.guid)
        self.assert_user_in_org_and_roles(test_user, TEST_ORG.guid, expected_roles)


@components(TAP.user_management, TAP.auth_gateway)
class DeleteOrganizationUser(BaseOrgUserClass):
    @classmethod
    def setUpClass(cls):
        cls.test_user = USERS[0]["user"]
        cls.test_client = USERS[0]["client"]
        cls.test_org = TEST_ORG

    @priority.high
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

    @priority.low
    def test_admin_cannot_delete_the_only_org_manager(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        roles = User.ORG_ROLES["manager"]
        self.step("Add user to organization as manager")
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        self.step("Check that the only manager cannot be removed from the organization")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            deleted_user.api_delete_from_organization, org_guid=org.guid)
        self.assert_user_in_org_and_roles(deleted_user, org.guid, roles)

    @priority.high
    def test_admin_deletes_one_of_org_users(self):
        not_deleted_user = self.test_user
        not_deleted_user_roles = User.ORG_ROLES["auditor"]
        deleted_user_roles = User.ORG_ROLES["billing_manager"]
        deleted_user = USERS[1]["user"]
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add two non-manager users to the organization")
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=deleted_user_roles)
        not_deleted_user.api_add_to_organization(org_guid=org.guid, roles=not_deleted_user_roles)
        self.step("Remove one of the users from the organization")
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self.assert_user_in_org_and_roles(not_deleted_user, org.guid, not_deleted_user_roles)
        self._assert_user_not_in_org(deleted_user, org.guid)

    @priority.low
    def test_admin_deletes_one_of_org_managers_cannot_delete_second(self):
        roles = User.ORG_ROLES["manager"]
        not_deleted_user = self.test_user
        deleted_user = USERS[1]["user"]
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add two managers to the organization")
        not_deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
        self.step("Remove one of the managers from the organization")
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self._assert_user_not_in_org(deleted_user, org.guid)
        self.step("Check that removing the last org manager returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                            not_deleted_user.api_delete_from_organization, org_guid=org.guid)
        self.assert_user_in_org_and_roles(not_deleted_user, org.guid, roles)

    @priority.low
    def test_admin_updates_role_of_one_org_manager_cannot_delete_second(self):
        manager_role = User.ORG_ROLES["manager"]
        for updated_user_roles in self.NON_MANAGER_ROLES:
            updated_user_roles = [updated_user_roles]
            with self.subTest(updated_rols=updated_user_roles):
                manager_user = self.test_user
                updated_user = USERS[1]["user"]
                self.step("Create a test organization")
                org = Organization.api_create()
                self.step("Add two managers to the organization")
                manager_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
                updated_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
                self.step("Update roles of one of the managers to {}".format(updated_user_roles))
                updated_user.api_update_org_roles(org_guid=org.guid, new_roles=updated_user_roles)
                self.assert_user_in_org_and_roles(updated_user, org.guid, updated_user_roles)
                self.step("Check that removing the last manger returns an error")
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                                    manager_user.api_delete_from_organization, org_guid=org.guid)
                self.assert_user_in_org_and_roles(manager_user, org.guid, manager_role)

    @priority.low
    def test_admin_cannot_delete_org_user_twice(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Add test user to organization")
        deleted_user.api_add_to_organization(org_guid=org.guid, roles=User.ORG_ROLES["auditor"])
        self.step("Delete test user from organization")
        deleted_user.api_delete_from_organization(org_guid=org.guid)
        self.step("Try to delete test user from organization second time")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY,
                                            deleted_user.api_delete_from_organization, org_guid=org.guid)

    @priority.low
    def test_admin_cannot_delete_non_existing_org_user(self):
        deleted_user = self.test_user
        self.step("Create a test organization")
        org = Organization.api_create()
        self.step("Check that an attempt to delete user which is not in org returns an error")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY,
                                            deleted_user.api_delete_from_organization, org_guid=org.guid)

    @priority.high
    def test_org_manager_can_delete_another_user(self):
        self.step("Create a test organization")
        org = Organization.api_create()
        manager_role = User.ORG_ROLES["manager"]
        self.step("Add org manager to organization")
        self.test_user.api_add_to_organization(org_guid=org.guid, roles=manager_role)
        user_client = self.test_client
        deleted_user = USERS[1]["user"]
        for roles in User.ORG_ROLES.values():
            with self.subTest(deleted_user_roles=roles):
                self.step("Add user to the test org with roles {}".format(roles))
                deleted_user.api_add_to_organization(org_guid=org.guid, roles=roles)
                self.step("Org manager removes the user from the test org")
                deleted_user.api_delete_from_organization(org_guid=org.guid, client=user_client)
                self._assert_user_not_in_org(deleted_user, org.guid)

    @priority.low
    def test_non_manager_cannot_delete_user(self):
        deleted_user_roles = User.ORG_ROLES["auditor"]
        non_manager_user, non_manager_client = self.test_user, self.test_client
        deleted_user = USERS[1]["user"]
        for non_manager_roles in self.NON_MANAGER_ROLES:
            non_manager_roles = [non_manager_roles]
            with self.subTest(non_manager_roles=non_manager_roles):
                self.step("Create a test organization")
                org = Organization.api_create()
                self.step("Add deleting user to the organization with roles {}".format(non_manager_roles))
                non_manager_user.api_add_to_organization(org_guid=org.guid, roles=non_manager_roles)
                self.step("Add deleted user to the organization with roles {}".format(deleted_user_roles))
                deleted_user.api_add_to_organization(org_guid=org.guid, roles=deleted_user_roles)
                self.step("Check that non-manager cannot delete user from org")
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    deleted_user.api_delete_from_organization, org_guid=org.guid,
                                                    client=non_manager_client)
                self.assert_user_in_org_and_roles(deleted_user, org.guid, deleted_user_roles)


@components(TAP.user_management)
class GetOrganizationUsers(BaseOrgUserClass):
    @classmethod
    def setUpClass(cls):
        cls.step("Create a test organization")
        cls.test_org = Organization.api_create()
        cls.step("Add new manager user to the test org")
        cls.manager = USERS[0]["user"]
        cls.manager.api_add_to_organization(org_guid=cls.test_org.guid, roles=User.ORG_ROLES["manager"])
        cls.manager_client = USERS[0]["client"]
        cls.step("Add non-manager users to the test org")
        cls.non_managers = {}
        cls.non_manager_clients = {}
        for index, roles in enumerate(cls.NON_MANAGER_ROLES):
            user = USERS[index + 1]["user"]
            user.api_add_to_organization(org_guid=cls.test_org.guid, roles=[roles])
            cls.non_managers[(roles,)] = user
            cls.non_manager_clients[roles] = USERS[index + 1]["client"]

    @priority.low
    def test_non_manager_in_org_cannot_get_org_users(self):
        for role, client in self.non_manager_clients.items():
            with self.subTest(user_role=role):
                self.step("Check that non-manager cannot get list of users in org")
                self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                                    User.api_get_list_via_organization, org_guid=self.test_org.guid,
                                                    client=client)

    @priority.high
    def test_manager_can_get_org_users(self):
        self.step("Check that manager can get list of users in org")
        expected_users = [self.manager] + list(self.non_managers.values())
        user_list = User.api_get_list_via_organization(org_guid=self.test_org.guid, client=self.manager_client)
        self.assertUnorderedListEqual(user_list, expected_users)

    @priority.low
    def test_user_not_in_org_cannot_get_org_users(self):
        self.step("Create new org")
        org = Organization.api_create()
        client = USERS[0]["client"]
        self.step("Check that the user cannot get list of users in the test org")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_FORBIDDEN, HttpStatus.MSG_FORBIDDEN,
                                            User.api_get_list_via_organization, org_guid=org.guid, client=client)

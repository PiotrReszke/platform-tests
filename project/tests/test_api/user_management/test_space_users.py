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
import time

from test_utils import ApiTestCase, cleanup_after_failed_setup, PlatformApiClient, platform_api_calls as api, \
    get_test_name
from objects import User, Organization, Space

USERS_CLIENTS = {}
TEST_ORG = None
TEST_SPACE = None
USER = None


def tearDownModule():
    User.cf_api_tear_down_test_users()
    User.api_tear_down_test_invitations()
    Organization.cf_api_tear_down_test_orgs()


@cleanup_after_failed_setup(tearDownModule)
def setUpModule():
    global USERS_CLIENTS, TEST_ORG, TEST_SPACE, USER
    TEST_ORG = Organization.api_create(space_names=("test_space",))
    USER = User.api_create_by_adding_to_organization(TEST_ORG.guid)
    other_test_org = Organization.api_create()
    TEST_SPACE = TEST_ORG.spaces[0]

    USERS_CLIENTS["admin"] = PlatformApiClient.get_admin_client()
    USERS_CLIENTS["org_manager"] = User.api_create_by_adding_to_organization(TEST_ORG.guid).login()
    USERS_CLIENTS["space_manager_in_org"] = User.api_create_by_adding_to_space(TEST_ORG.guid, TEST_SPACE.guid).login()
    USERS_CLIENTS["org_user"] = User.api_create_by_adding_to_organization(TEST_ORG.guid,
                                                                          roles=User.ORG_ROLES["auditor"]).login()
    USERS_CLIENTS["other_org_manager"] = User.api_create_by_adding_to_organization(other_test_org.guid).login()
    USERS_CLIENTS["other_user"] = User.api_create_by_adding_to_organization(other_test_org.guid, roles=[]).login()


class BaseSpaceUserClass(ApiTestCase):
    ALL_ROLES = {role for role_set in User.ORG_ROLES.values() for role in role_set}
    NON_MANAGER_ROLES = ALL_ROLES - User.ORG_ROLES["manager"]
    ALL_SPACE_ROLES = {role for role_set in User.SPACE_ROLES.values() for role in role_set}
    NON_MANAGER_SPACE_ROLES = ALL_SPACE_ROLES - User.SPACE_ROLES["manager"]

    @classmethod
    def tearDownClass(cls):
        # silence tearDownClass method inherited from ApiTestCase class, so users are not deleted before tearDownModule
        pass

    def _assert_user_in_space_with_roles(self, expected_user, space_guid):
        self.step("Check that the user is on the list of space users")
        space_users = User.api_get_list_via_space(space_guid)
        self.assertInList(expected_user, space_users)
        space_user = next(user for user in space_users if user.guid == expected_user.guid)
        self.step("Check that the user has expected space roles")
        space_user_roles = space_user.space_roles.get(space_guid)
        expected_roles = expected_user.space_roles.get(space_guid)
        self.assertUnorderedListEqual(space_user_roles, expected_roles,
                                      "{} space roles are not equal".format(expected_user))

    def _assert_user_not_in_space(self, expected_user, space_guid):
        self.step("Check that the user is not on the space user list")
        space_users = User.api_get_list_via_space(space_guid)
        user_who_should_not_be_in_space = next((user for user in space_users if user.guid == expected_user.guid), None)
        self.assertIsNone(user_who_should_not_be_in_space, "Unexpectedly, {} was found in space".format(expected_user))


class GetSpaceUsers(BaseSpaceUserClass):
    @classmethod
    def setUpClass(cls):
        cls.test_space = Space.api_create(TEST_ORG)

    def test_get_user_list_from_deleted_space(self):
        self.step("Delete the space")
        self.test_space.cf_api_delete()
        self.step("Check that retrieving list of users in the deleted space returns an error")
        self.assertRaisesUnexpectedResponse(404, "Not Found", User.api_get_list_via_space, self.test_space.guid)


class AddNewUserToSpace(BaseSpaceUserClass):
    def test_add_non_existing_user_to_space(self):
        """DPNG-2287 Cannot register as a new user added to space"""
        self.step("Create new platform user with each role by adding him to space")
        for space_role in self.ALL_SPACE_ROLES:
            with self.subTest(space_role=space_role):
                new_user = User.api_create_by_adding_to_space(TEST_ORG.guid, TEST_SPACE.guid, roles=[space_role])
                self._assert_user_in_space_with_roles(new_user, TEST_SPACE.guid)

    def test_cannot_add_new_user_with_no_roles(self):
        self.assertRaisesUnexpectedResponse(409, "You must have at least one role", User.api_create_by_adding_to_space,
                                            TEST_ORG.guid, TEST_SPACE.guid, roles=[])

    @unittest.expectedFailure
    def test_cannot_create_new_user_with_long_username(self):
        """DPNG-3363 Api email validation does not work properly"""
        long_username = User.TEST_EMAIL_FORM.format(str(time.time()) + "x" * 300)
        self.assertRaisesUnexpectedResponse(400, "", User.api_create_by_adding_to_space, TEST_ORG.guid,
                                            TEST_SPACE.guid, username=long_username)

    def test_cannot_create_new_user_with_non_email_username(self):
        non_email = "non_email_username"
        self.assertRaisesUnexpectedResponse(409, "That email address is not valid", User.api_create_by_adding_to_space,
                                            TEST_ORG.guid, TEST_SPACE.guid, username=non_email)

    def test_cannot_create_user_with_existing_username(self):
        test_user = User.api_create_by_adding_to_space(TEST_ORG.guid, TEST_SPACE.guid)
        # api returns no error message
        self.assertRaisesUnexpectedResponse(403, "", User.api_create_by_adding_to_space, TEST_ORG.guid, TEST_SPACE.guid,
                                            username=test_user.username)

    def test_cannot_create_user_with_special_characters_username(self):
        test_username = get_test_name(email=True)
        test_username = test_username.replace("@", "\n\t@")
        self.assertRaisesUnexpectedResponse(409, "That email address is not valid", User.api_create_by_adding_to_space,
                                            TEST_ORG.guid, TEST_SPACE.guid, username=test_username)

    @unittest.expectedFailure
    def test_cannot_create_user_with_non_ascii_characters_username(self):
        """DPNG-3583 Http 500 when email contains non ascii characters"""
        test_username = get_test_name(email=True)
        test_username = test_username.replace("@", "ąśćżźł@")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", User.api_create_by_adding_to_space, TEST_ORG.guid,
                                            TEST_SPACE.guid, username=test_username)

    def test_cannot_add_new_user_to_non_existing_space(self):
        space_guid = "this-space-guid-is-not-correct"
        self.step("Check that an error is raised when trying to add user using incorrect space guid")
        self.assertRaisesUnexpectedResponse(400, "Wrong uuid format exception", User.api_create_by_adding_to_space,
                                            TEST_ORG.guid, space_guid)

    def test_cannot_add_new_user_with_incorrect_role(self):
        space_users = User.api_get_list_via_space(TEST_SPACE.guid)
        roles = ["i-don't-exist"]
        self.step("Check that error is raised when trying to add user using incorrect roles")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", User.api_create_by_adding_to_space, TEST_ORG.guid,
                                            TEST_SPACE.guid, roles=roles)
        self.step("Assert user list did not change")
        self.assertListEqual(User.api_get_list_via_space(TEST_SPACE.guid), space_users,
                             "User with incorrect roles was added to space")


class AddExistingUserToSpace(BaseSpaceUserClass):
    def setUp(self):
        self.step("Create test space")
        self.test_space = Space.api_create(TEST_ORG)

    def test_add_existing_users_with_one_role(self):
        for space_role in self.ALL_SPACE_ROLES:
            with self.subTest(space_role=space_role):
                self.step("Create new platform user by adding to the organization")
                test_user = User.api_create_by_adding_to_organization(TEST_ORG.guid)
                self.step("Add the user to space with role {}".format(space_role))
                test_user.api_add_to_space(self.test_space.guid, TEST_ORG.guid, roles=[space_role])
                self._assert_user_in_space_with_roles(test_user, self.test_space.guid)

    def test_add_existing_user_without_roles(self):
        """DPNG-2281 It's possible to add user to space without any roles using API"""
        self.step("Check that attempt to add user to space with no roles returns an error")
        self.assertRaisesUnexpectedResponse(409, "You must have at least one role", USER.api_add_to_space,
                                            self.test_space.guid, TEST_ORG.guid, roles=())
        self._assert_user_not_in_space(USER, self.test_space.guid)

    def test_add_existing_user_with_all_available_roles(self):
        self.step("Add the user to space with roles {}".format(self.ALL_SPACE_ROLES))
        USER.api_add_to_space(self.test_space.guid, TEST_ORG.guid, roles=self.ALL_SPACE_ROLES)
        self._assert_user_in_space_with_roles(USER, self.test_space.guid)

    def test_cannot_add_existing_user_to_non_existing_space(self):
        invalid_space_guid = "invalid-space-guid"
        self.step("Check that it is not possible to add existing user to not existing space")
        self.assertRaisesUnexpectedResponse(400, "Wrong uuid format exception", USER.api_add_to_space,
                                            invalid_space_guid, TEST_ORG.guid, roles=self.ALL_SPACE_ROLES)

    def test_cannot_add_existing_user_with_incorrect_role(self):
        invalid_role = ["incorrect-role"]
        self.step("Check that it is not possible to add existing user to space with invalid space role")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", USER.api_add_to_space, self.test_space.guid,
                                            TEST_ORG.guid, roles=invalid_role)


class UpdateSpaceUser(BaseSpaceUserClass):
    def setUp(self):
        self.step("Create test space")
        self.test_space = Space.api_create(TEST_ORG)

    def test_change_user_role(self):
        initial_roles = User.SPACE_ROLES["manager"]
        new_roles = User.SPACE_ROLES["auditor"]
        self.step("Add user to space with roles {}".format(initial_roles))
        USER.api_add_to_space(space_guid=self.test_space.guid, org_guid=TEST_ORG.guid, roles=initial_roles)
        self.step("Update the user, change their role to {}".format(new_roles))
        USER.api_update_space_roles(self.test_space.guid, new_roles=new_roles)
        self._assert_user_in_space_with_roles(USER, self.test_space.guid)

    def test_cannot_change_role_to_invalid_one(self):
        initial_roles = User.SPACE_ROLES["manager"]
        new_roles = ("wrong_role",)
        self.step("Add user to space with roles {}".format(initial_roles))
        USER.api_add_to_space(space_guid=self.test_space.guid, org_guid=TEST_ORG.guid, roles=initial_roles)
        self.step("Check that updating space user roles to invalid ones returns an error")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", USER.api_update_space_roles,
                                            self.test_space.guid, new_roles=new_roles)
        self._assert_user_in_space_with_roles(USER, self.test_space.guid)

    def test_delete_user_roles_while_in_space(self):
        # deleting all roles deletes user from the space, but the user remains in the organization
        self.step("Add user to space")
        USER.api_add_to_space(space_guid=self.test_space.guid, org_guid=TEST_ORG.guid)
        self.step("Update the user, removing all space roles")
        USER.api_update_space_roles(self.test_space.guid, new_roles=())
        self._assert_user_not_in_space(USER, self.test_space.guid)
        self.step("Check that the user is still in the organization")
        org_users = User.api_get_list_via_organization(org_guid=TEST_ORG.guid)
        self.assertInList(USER, org_users, "User is not in the organization")

    def test_cannot_update_user_which_is_not_in_space(self):
        user_not_in_space = USER
        self.step("Create test space")
        space = Space.api_create(TEST_ORG)
        self.step("Check that attempt to update a user via space they are not in returns an error.")
        space_users = User.api_get_list_via_space(space.guid)
        self.assertRaisesUnexpectedResponse(404, "User {} does not exist in space {}".format(user_not_in_space.guid,
                                                                                             space.guid),
                                            user_not_in_space.api_update_space_roles, space.guid,
                                            new_roles=User.SPACE_ROLES["auditor"])
        self.assertListEqual(User.api_get_list_via_space(space.guid), space_users)

    def test_cannot_update_non_existing_space_user(self):
        invalid_guid = "invalid-user-guid"
        roles = User.SPACE_ROLES["auditor"]
        self.step("Check that updating user which is not in space returns error")
        space_users = User.api_get_list_via_space(self.test_space.guid)
        self.assertRaisesUnexpectedResponse(400, "Wrong uuid format exception", api.api_update_space_user_roles,
                                            self.test_space.guid, invalid_guid, roles)
        self.assertListEqual(User.api_get_list_via_space(self.test_space.guid), space_users)

    def test_cannot_update_space_user_in_not_existing_space(self):
        invalid_guid = "invalid-space_guid"
        roles = User.SPACE_ROLES["auditor"]
        self.step("Check that updating user using invalid space guid return an error")
        self.assertRaisesUnexpectedResponse(400, "Wrong uuid format exception", api.api_update_space_user_roles,
                                            invalid_guid, USER.guid, roles)


class DeleteSpaceUser(BaseSpaceUserClass):
    def setUp(self):
        self.step("Create test space")
        self.test_space = Space.api_create(TEST_ORG)

    def test_delete_user_from_space(self):
        self.step("Add the user to space")
        USER.api_add_to_space(self.test_space.guid, TEST_ORG.guid)
        self.step("Delete the user from space")
        USER.api_delete_from_space(self.test_space.guid)
        self._assert_user_not_in_space(USER, self.test_space.guid)
        self.step("Check that the user is still in the organization")
        org_users = User.api_get_list_via_organization(org_guid=TEST_ORG.guid)
        self.assertInList(USER, org_users, "User is not in the organization")

    def test_delete_user_which_is_not_in_space(self):
        """DPNG-2293 Deleting from space a user which is not in this space does not return any error"""
        self.step("Check that deleting the user from space they are not in returns an error")
        self.assertRaisesUnexpectedResponse(404, "The user is not in given space", USER.api_delete_from_space,
                                            self.test_space.guid)


class SpaceUserPermissions(BaseSpaceUserClass):
    @classmethod
    def setUpClass(cls):
        cls.client_permission = {
            "admin": True,
            "org_manager": True,
            "space_manager_in_org": True,
            "org_user": False,
            "other_org_manager": False,
            "other_user": False
        }

    def test_get_user_list(self):
        test_user = User.api_create_by_adding_to_space(TEST_ORG.guid, TEST_SPACE.guid)
        self.step("Try to get user list from space by using every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                if is_authorized:
                    user_list = User.api_get_list_via_space(TEST_SPACE.guid, client=USERS_CLIENTS[client])
                    self.assertInList(test_user, user_list, "User {} was not found in list".format(test_user))
                else:
                    self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                        User.api_get_list_via_space, TEST_SPACE.guid,
                                                        client=USERS_CLIENTS[client])

    def test_add_new_user(self):
        self.step("Try to add new user with every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                user_list = User.api_get_list_via_space(TEST_SPACE.guid)
                if is_authorized:
                    test_user = User.api_create_by_adding_to_space(TEST_ORG.guid, TEST_SPACE.guid,
                                                                   inviting_client=USERS_CLIENTS[client])
                    self._assert_user_in_space_with_roles(test_user, TEST_SPACE.guid)
                else:
                    self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                        User.api_create_by_adding_to_space, TEST_ORG.guid,
                                                        TEST_SPACE.guid, inviting_client=USERS_CLIENTS[client])
                    self.assertUnorderedListEqual(User.api_get_list_via_space(TEST_SPACE.guid), user_list,
                                                  "User was added")

    def test_add_existing_user(self):
        self.step("Try to add existing user to space with every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(user_type=client):
                if is_authorized:
                    test_user = User.api_create_by_adding_to_organization(TEST_ORG.guid)
                    test_user.api_add_to_space(TEST_SPACE.guid, TEST_ORG.guid, client=USERS_CLIENTS[client])
                    self._assert_user_in_space_with_roles(test_user, TEST_SPACE.guid)
                else:
                    self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                        User.api_create_by_adding_to_space, TEST_ORG.guid,
                                                        TEST_SPACE.guid, inviting_client=USERS_CLIENTS[client])

    def test_update_role(self):
        new_roles = User.SPACE_ROLES["auditor"]
        self.step("Try to change user space role using every client type.")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(userType=client):
                test_user = User.api_create_by_adding_to_space(TEST_ORG.guid, TEST_SPACE.guid,
                                                               roles=User.SPACE_ROLES["developer"])
                if is_authorized:
                    test_user.api_update_space_roles(TEST_SPACE.guid, new_roles=new_roles, client=USERS_CLIENTS[client])
                    self._assert_user_in_space_with_roles(test_user, TEST_SPACE.guid)
                else:
                    self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                        test_user.api_update_space_roles, TEST_SPACE.guid,
                                                        new_roles=new_roles, client=USERS_CLIENTS[client])
                    self.assertListEqual(test_user.space_roles.get(TEST_SPACE.guid),
                                         list(User.SPACE_ROLES["developer"]), "User roles were updated")

    def test_delete_user(self):
        self.step("Try to delete user from space using every client type")
        for client, is_authorized in self.client_permission.items():
            with self.subTest(userType=client):
                test_user = User.api_create_by_adding_to_space(TEST_ORG.guid, TEST_SPACE.guid)
                self._assert_user_in_space_with_roles(test_user, TEST_SPACE.guid)
                if is_authorized:
                    test_user.api_delete_from_space(TEST_SPACE.guid, client=USERS_CLIENTS[client])
                    self._assert_user_not_in_space(test_user, TEST_SPACE.guid)
                else:
                    self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                        test_user.api_delete_from_space, TEST_SPACE.guid,
                                                        client=USERS_CLIENTS[client])
                    self.assertInList(test_user, User.api_get_list_via_space(TEST_SPACE.guid), "User was deleted")

    def test_add_space(self):
        client_permission = {
            "admin": True,
            "org_manager": True,
            "space_manager_in_org": False,
            "org_user": False,
            "other_org_manager": False,
            "other_user": False
        }
        self.step("Try to add new space using every client type.")
        for client in USERS_CLIENTS:
            with self.subTest(userType=client):
                space_list = TEST_ORG.api_get_spaces()
                if client_permission[client]:
                    new_space = Space.api_create(TEST_ORG, client=USERS_CLIENTS[client])
                    space_list = Space.api_get_list()
                    self.assertInList(new_space, space_list, "Space was not created.")
                else:
                    self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                        Space.api_create, TEST_ORG, client=USERS_CLIENTS[client])
                    self.assertUnorderedListEqual(TEST_ORG.api_get_spaces(), space_list, "Space was created")

    def test_delete_space(self):
        client_permission = {
            "admin": True,
            "org_manager": True,
            "space_manager_in_org": False,
            "org_user": False,
            "other_org_manager": False,
            "other_user": False
        }
        self.step("Try to delete space using every client type.")
        for client in USERS_CLIENTS:
            with self.subTest(userType=client):
                new_space = Space.api_create(TEST_ORG)
                if client_permission[client]:
                    new_space.api_delete(TEST_ORG, client=USERS_CLIENTS[client])
                    self.assertNotInListWithRetry(new_space, Space.api_get_list)
                else:
                    self.assertRaisesUnexpectedResponse(403, "You are not authorized to perform the requested action",
                                                        new_space.api_delete, TEST_ORG, client=USERS_CLIENTS[client])
                    self.assertInList(new_space, TEST_ORG.api_get_spaces(), "Space was not deleted")

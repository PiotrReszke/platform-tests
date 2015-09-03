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

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import Organization, User


class TestOrganizationUsers(ApiTestCase):

    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()

    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUp(self):
        self.organization = Organization.api_create()
        User.get_admin().api_add_to_organization(org_guid=self.organization.guid)
        self.test_user, _, self.test_user_client = User.api_onboard()
        self.test_user.api_add_to_organization(self.organization.guid, roles=("managers",))

    def test_create_organization_user_with_role(self):
        """Create a user with each of the roles allowed"""
        for role in ["managers", "auditors", "billing_managers"]:
            with self.subTest(role=role):
                expected_roles = [role]
                self.test_user.api_add_to_organization(self.organization.guid, roles=expected_roles)
                users = User.api_get_list_via_organization(self.organization.guid)
                self.assertInList(self.test_user, users)
                user_roles = self.test_user.org_roles.get(self.organization.guid)
                self.assertEqual(user_roles, expected_roles)

    def test_create_organization_user(self):
        """Verify that each, admin and organization manager, can create an organization user"""
        for client in [self.test_user_client, None]:
            with self.subTest(client=client):
                expected_roles = ["managers"]
                self.test_user.api_add_to_organization(self.organization.guid, client=client, roles=expected_roles)
                users = User.api_get_list_via_organization(self.organization.guid, client=client)
                self.assertInList(self.test_user, users)
                roles = self.test_user.org_roles.get(self.organization.guid)
                self.assertEqual(roles, expected_roles)

    def test_create_organization_user_two_roles(self):
        expected_roles = ["managers", "auditors"]
        self.test_user.api_add_to_organization(self.organization.guid, roles=expected_roles)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        roles = self.test_user.org_roles.get(self.organization.guid)
        self.assertEqual(roles, expected_roles)

    def test_create_organization_user_all_roles(self):
        expected_roles = ["managers", "auditors", "billing_managers"]
        self.test_user.api_add_to_organization(self.organization.guid, roles=expected_roles)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        roles = self.test_user.org_roles.get(self.organization.guid)
        self.assertEqual(roles, expected_roles)

    def test_create_organization_user_incorrect_role(self):
        self.assertRaisesUnexpectedResponse(400, "", self.test_user.api_add_to_organization,
                                            org_guid=self.organization.guid, roles=["i-don't-exist"])

    def test_update_organization_user_add_role(self):
        roles = ["managers"]
        new_roles = ["managers", "auditors"]
        self.test_user.api_add_to_organization(self.organization.guid, roles=roles)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        self.assertEqual(self.test_user.org_roles.get(self.organization.guid), roles)
        self.test_user.api_update_via_organization(org_guid=self.organization.guid, new_roles=new_roles)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        user_roles = self.test_user.org_roles.get(self.organization.guid)
        self.assertEqual(user_roles, new_roles)

    def test_update_organization_user_remove_role(self):
        roles = ["managers", "billing_managers"]
        new_roles = ["managers"]
        self.test_user.api_add_to_organization(self.organization.guid, roles=roles)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        self.assertEqual(self.test_user.org_roles.get(self.organization.guid), roles)
        self.test_user.api_update_via_organization(org_guid=self.organization.guid, new_roles=new_roles)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        user_roles = self.test_user.org_roles.get(self.organization.guid)
        self.assertEqual(user_roles, new_roles)

    def test_update_organization_user_change_role(self):
        roles = ["managers"]
        new_roles = ["auditors"]
        self.test_user.api_add_to_organization(self.organization.guid, roles=roles)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        self.assertEqual(self.test_user.org_roles.get(self.organization.guid), roles)
        self.test_user.api_update_via_organization(org_guid=self.organization.guid, new_roles=new_roles)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        user_roles = self.test_user.org_roles.get(self.organization.guid)
        self.assertEqual(user_roles, new_roles)

    def test_delete_organization_user(self):
        self.test_user.api_add_to_organization(self.organization.guid)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertInList(self.test_user, users)
        self.test_user.api_delete_via_organization(self.organization.guid)
        users = User.api_get_list_via_organization(self.organization.guid)
        self.assertNotInList(self.test_user, users)




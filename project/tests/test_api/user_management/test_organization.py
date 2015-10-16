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

from test_utils import ApiTestCase, get_logger
from objects import Organization, User


logger = get_logger("test organization")


class TestOrganization(ApiTestCase):

    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()

    def test_create_organization(self):
        self.step("Create an organization")
        expected_org = Organization.api_create()
        self.step("Check that the organization is on the organization list")
        orgs = Organization.api_get_list()
        self.assertInList(expected_org, orgs)

    def test_rename_organization(self):
        self.step("Create an organization")
        expected_org = Organization.api_create()
        self.step("Update the organization, giving it new name")
        new_name = "new-{}".format(expected_org.name)
        expected_org.rename(new_name)
        self.step("Check that the organization with new name is on the organization list")
        orgs = Organization.api_get_list()
        self.assertInList(expected_org, orgs)

    def test_delete_organization(self):
        self.step("Create an organization")
        deleted_org = Organization.api_create()
        self.step("Check that the organization is on the org list")
        orgs = Organization.api_get_list()
        self.assertInList(deleted_org, orgs)
        self.step("Delete the organization")
        deleted_org.api_delete()
        self.step("Check that the organization is not on org list")
        orgs = Organization.api_get_list()
        self.assertNotInList(deleted_org, orgs)

    def test_get_more_than_50_organizations(self):
        self.step("Get list of organization and check how many there are")
        old_orgs = Organization.api_get_list()
        orgs_num = len(old_orgs)
        self.step("Add organizations, so that there are more than 50")
        new_orgs_num = (50 - orgs_num) + 1
        new_orgs = [Organization.api_create() for _ in range(new_orgs_num)]
        self.step("Check that all new and old organizations are returned in org list")
        expected_orgs = old_orgs + new_orgs
        orgs = Organization.api_get_list()
        self.assertEqual(len(orgs), len(expected_orgs))
        self.assertUnorderedListEqual(orgs, expected_orgs)

    def test_delete_organization_with_user(self):
        self.step("Create an organization")
        org = Organization.api_create()
        self.step("Add new platform user to the organization")
        User.api_create_by_adding_to_organization(org.guid)
        self.step("Delete the organization")
        org.api_delete()
        self.step("Check that the organization is not on org list")
        org_list = Organization.api_get_list()
        self.assertNotInList(org, org_list, "Organization with user was not deleted.")

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

from objects import Organization
from test_utils import ApiTestCase, get_logger


logger = get_logger("test organization")


class TestOrganization(ApiTestCase):

    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()

    def test_get_organization_list(self):
        orgs = Organization.api_get_list()
        logger.info("There are {} organizations".format(len(orgs)))
        self.assertTrue(len(orgs) > 0)

    def test_create_organization(self):
        expected_org = Organization.api_create()
        orgs = Organization.api_get_list()
        self.assertInList(expected_org, orgs)

    def test_rename_organization(self):
        expected_org = Organization.api_create()
        orgs = Organization.api_get_list()
        self.assertInList(expected_org, orgs)
        new_name = "new-{}".format(expected_org.name)
        expected_org.rename(new_name)
        orgs = Organization.api_get_list()
        self.assertInList(expected_org, orgs)

    def test_delete_organization(self):
        deleted_org = Organization.api_create()
        orgs = Organization.api_get_list()
        self.assertInList(deleted_org, orgs)
        deleted_org.api_delete()
        orgs = Organization.api_get_list()
        self.assertNotInList(deleted_org, orgs)

    def test_get_more_than_50_organizations(self):
        old_orgs = Organization.api_get_list()
        orgs_num = len(old_orgs)
        new_orgs_num = (50 - orgs_num) + 1
        new_orgs = [Organization.api_create() for _ in range(new_orgs_num)]
        expected_orgs = old_orgs + new_orgs
        orgs = Organization.api_get_list()
        self.assertEqual(len(orgs), len(expected_orgs))
        self.assertCountEqual(orgs, expected_orgs)


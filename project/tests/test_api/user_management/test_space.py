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

from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup
from objects import Organization, Space, User


logger = get_logger("test spaces")


class BaseTestSpaceClass(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.test_org = Organization.api_create()

    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()


class GetSpaces(BaseTestSpaceClass):

    def test_get_spaces_list_in_new_org(self):
        org = Organization.api_create()
        spaces = org.api_get_spaces()
        logger.info("There are {} spaces in org {}".format(len(spaces), org.name))
        self.assertEqual(len(spaces), 0)

    def test_get_spaces_list_in_org(self):
        spaces = Space.api_get_list()
        Space.api_create(org=self.test_org)
        new_spaces = Space.api_get_list()
        logger.info("There are {} spaces in org {}".format(len(spaces), self.test_org.name))
        self.assertEqual(len(spaces)+1, len(new_spaces))


class CreateSpace(BaseTestSpaceClass):

    def test_create_space(self):
        space = Space.api_create(org=self.test_org)
        logger.info("Created space {}".format(space.name))
        spaces = Space.api_get_list()
        self.assertInList(space, spaces)

    def test_cannot_create_space_with_existing_name(self):
        space = Space.api_create(org=self.test_org)
        logger.info("Attempting to create space {}".format(space.name))
        self.assertRaisesUnexpectedResponse(400, "Bad Request", Space.api_create, org=self.test_org, name=space.name)

    def test_create_space_with_long_name(self):
        long_name = Space.NAME_PREFIX + "t" * 400
        space = Space.api_create(org=self.test_org, name=long_name)
        spaces = Space.api_get_list()
        self.assertInList(space, spaces)

    def test_create_space_with_empty_name(self):
        self.assertRaisesUnexpectedResponse(400, "Bad Request", Space.api_create, name="", org=self.test_org)


class DeleteSpace(BaseTestSpaceClass):

    def test_delete_space(self):
        space = Space.api_create(org=self.test_org)
        spaces = Space.api_get_list()
        self.assertInList(space, spaces)
        logger.info("Created space {}".format(space.name))
        space.api_delete(org=self.test_org)
        spaces = Space.api_get_list()
        logger.info("Deleted space {}".format(space.name))
        self.assertNotInList(space, spaces)

    def test_cannot_delete_not_existing_space(self):
        space = Space.api_create(org=self.test_org)
        space.api_delete(org=self.test_org)
        self.assertRaisesUnexpectedResponse(404, "Not Found", space.api_delete, org=self.test_org)

    @unittest.expectedFailure
    def test_cannot_delete_space_with_user(self):
        """DPNG-2246 An space with user can be deleted"""
        test_user = User.api_create_by_adding_to_organization(self.test_org.guid)
        space = Space.api_create(org=self.test_org)
        test_user.api_add_to_space(space.guid, self.test_org.guid)
        space.api_delete(org=self.test_org)
        spaces = Space.api_get_list()
        self.assertInList(space, spaces, "Space that contained user, was deleted.")

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

from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup
from objects import Organization, Space


logger = get_logger("test spaces")


class TestSpace(ApiTestCase):

    ORG_NAME = "seedorg"
    SPACE_NAME = "seedspace"

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.org = Organization.api_create()

    def test_get_spaces_list(self):
        spaces = Space.api_get_list()
        logger.info("There are {} spaces".format(len(spaces)))
        self.assertNotEqual(len(spaces), 0)

    def test_get_spaces_list_in_org(self):
        spaces = Space.api_get_list()
        Space.api_create(org=self.org)
        new_spaces = Space.api_get_list()
        logger.info("There are {} spaces in org {}".format(len(spaces), self.org.name))
        self.assertEqual(len(spaces)+1, len(new_spaces))

    def test_get_spaces_list_in_empty_org(self):
        org = Organization.api_create()
        spaces = org.api_get_spaces()
        logger.info("There are {} spaces in org {}".format(len(spaces), org.name))
        self.assertEqual(len(spaces), 0)

    def test_create_space(self):
        space = Space.api_create(org=self.org)
        logger.info("Created space {}".format(space.name))
        spaces = Space.api_get_list()
        self.assertInList(space, spaces)

    def test_create_space_with_existing_name(self):
        space = Space.api_create(org=self.org)
        logger.info("Attempting to create space {}".format(space.name))
        self.assertRaisesUnexpectedResponse(400, None, Space.api_create, org=self.org, name=space.name)

    def test_delete_space(self):
        space = Space.api_create(org=self.org)
        spaces = Space.api_get_list()
        self.assertInList(space, spaces)
        logger.info("Created space {}".format(space.name))
        space.api_delete(org=self.org)
        spaces = Space.api_get_list()
        logger.info("Deleted space {}".format(space.name))
        self.assertNotInList(space, spaces)


from test_utils.objects import Organization, Space
from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup



logger = get_logger("test spaces")


class TestSpace(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.api_delete_test_orgs)
    def setUpClass(cls):
        cls.org = Organization.create()

    @classmethod
    def tearDownClass(cls):
        Organization.api_delete_test_orgs()

    def test_get_spaces_list(self):
        spaces = Space.api_get_list()
        logger.info("There are {} spaces".format(len(spaces)))
        self.assertTrue(len(spaces) > 0)

    def test_get_spaces_list_in_org(self):
        spaces = Space.api_get_list()
        Space.api_create(org=self.org)
        new_spaces = Space.api_get_list()
        logger.info("There are {} spaces in org {}".format(len(spaces), self.org.name))
        self.assertEqual(len(spaces)+1, len(new_spaces))

    def test_get_spaces_list_in_empty_org(self):
        org = Organization.create()
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


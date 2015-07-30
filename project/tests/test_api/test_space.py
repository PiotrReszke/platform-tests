from test_utils.objects import Organization, Space
from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup



logger = get_logger("test spaces")


class TestSpace(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.delete_test_orgs)
    def setUpClass(cls):
        cls.org = Organization.create()

    @classmethod
    def tearDownClass(cls):
        Organization.delete_test_orgs()

    def test_get_spaces_list(self):
        spaces = Space.get_list()
        logger.info("There are {} spaces".format(len(spaces)))
        self.assertTrue(len(spaces) > 0)

    def test_get_spaces_list_in_org(self):
        spaces = Space.get_list(org_guid=self.org.guid)
        Space.create(org_guid=self.org.guid)
        new_spaces = Space.get_list(org_guid=self.org.guid)
        logger.info("There are {} spaces in org {}".format(len(spaces), self.org.name))
        self.assertEqual(len(spaces)+1, len(new_spaces))

    def test_get_spaces_list_in_empty_org(self):
        org = Organization.create()
        spaces = Space.get_list(org_guid=org.guid)
        logger.info("There are {} spaces in org {}".format(len(spaces), org.name))
        self.assertEqual(len(spaces), 0)

    def test_create_space(self):
        space = Space.create(org_guid=self.org.guid)
        logger.info("Created space {}".format(space.name))
        spaces = Space.get_list(org_guid=self.org.guid)
        self.assertInList(space, spaces)

    def test_create_space_with_existing_name(self):
        space = Space.create(org_guid=self.org.guid)
        logger.info("Attempting to create space {}".format(space.name))
        self.assertRaisesUnexpectedResponse(400, None, Space.create, org_guid=self.org.guid, name=space.name)

    def test_delete_space(self):
        space = Space.create(org_guid=self.org.guid)
        spaces = Space.get_list(org_guid=self.org.guid)
        self.assertInList(space, spaces)
        logger.info("Created space {}".format(space.name))
        space.delete()
        spaces = Space.get_list(org_guid=self.org.guid)
        logger.info("Deleted space {}".format(space.name))
        self.assertNotInList(space, spaces)


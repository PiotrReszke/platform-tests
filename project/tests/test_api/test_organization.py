from test_utils import Organization, ApiTestCase, get_logger

logger = get_logger("test organization")


class TestOrganization(ApiTestCase):

    @classmethod
    def tearDownClass(cls):
        Organization.delete_test_orgs()

    def test_get_organization_list(self):
        orgs = Organization.get_list()
        logger.info("There are {} organizations".format(len(orgs)))
        self.assertTrue(len(orgs) > 0)

    def test_create_organization(self):
        expected_org = Organization.create()
        orgs = Organization.get_list()
        self.assertInList(expected_org, orgs)

    def test_rename_organization(self):
        expected_org = Organization.create()
        orgs = Organization.get_list()
        self.assertInList(expected_org, orgs)
        new_name = "new-{}".format(expected_org.name)
        expected_org.rename(new_name)
        orgs = Organization.get_list()
        self.assertInList(expected_org, orgs)

    def test_delete_organization(self):
        deleted_org = Organization.create()
        orgs = Organization.get_list()
        self.assertInList(deleted_org, orgs)
        deleted_org.delete()
        orgs = Organization.get_list()
        self.assertNotInList(deleted_org, orgs)

    def test_get_more_than_50_organizations(self):
        old_orgs = Organization.get_list()
        orgs_num = len(old_orgs)
        new_orgs_num = (50 - orgs_num) + 1
        new_orgs = [Organization.create() for x in range(new_orgs_num)]
        expected_orgs = old_orgs + new_orgs
        orgs = Organization.get_list()
        self.assertTrue(len(orgs), len(expected_orgs))
        self.assertListEqual(sorted(orgs), sorted(expected_orgs))
from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger
from test_utils import Organization, Transfer, User


logger = get_logger("test data transfer")


class TestDataTransfer(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.delete_test_orgs)
    def setUpClass(cls):
        cls.org = Organization.create()
        cls.org.add_admin()

    def test_get_transfers(self):
        transfers = Transfer.get_list(orgs=[self.org])
        logger.info("{} transfers".format(len(transfers)))

    def test_submit_transfer(self):
        data_source = "http://fake-csv-server.apps.gotapaas.eu/fake-csv/100"
        expected_transfer = Transfer.create(source=data_source, org_guid=self.org.guid)
        transfer = Transfer.get(expected_transfer.id)
        x = 0



from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger
from test_utils.objects import Organization, Transfer, DataSet


logger = get_logger("test data transfer")


class TestDataTransfer(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.api_delete_test_orgs)
    def setUpClass(cls):
        cls.org = Organization.create()
        cls.org.add_admin()

    def test_get_transfers(self):
        transfers = Transfer.api_get_list(orgs=[self.org])
        logger.info("{} transfers".format(len(transfers)))

    def test_submit_transfer(self):
        data_source = Transfer.get_test_transfer_link()
        expected_transfer = Transfer.api_create(source=data_source, org_guid=self.org.guid)
        expected_transfer.ensure_finished()
        transfer = Transfer.api_get(expected_transfer.id)
        self.assertAttributesEqual(transfer, expected_transfer)

    def test_match_dataset_to_transfer(self):
        data_source = Transfer.get_test_transfer_link()
        expected_transfer = Transfer.api_create(source=data_source, org_guid=self.org.guid)
        expected_transfer.ensure_finished()
        transfers = Transfer.api_get_list(orgs=[self.org])
        self.assertInList(expected_transfer, transfers)
        dataset = DataSet.api_get_matching_to_transfer(org_list=[self.org], transfer=expected_transfer)
        datasets_data = DataSet.api_get_list_and_metadata(org_list=[self.org])
        datasets = datasets_data["data_sets"]
        self.assertInList(dataset, datasets)


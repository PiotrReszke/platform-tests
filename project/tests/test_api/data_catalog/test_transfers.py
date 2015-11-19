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

import time

from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger, platform_api_calls as api, \
    generate_csv_file, tear_down_test_files
from objects import Organization, Transfer, DataSet, User


logger = get_logger("test data transfer")


class SubmitTransfer(ApiTestCase):

    EXAMPLE_LINK = "http://fake-csv-server.gotapaas.eu/fake-csv/2"

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    def test_admin_can_get_transfer_list(self):
        self.step("Check if the list of transfers can be retrieved")
        transfers = Transfer.api_get_list(org_list=[self.org])
        logger.info("{} transfers".format(len(transfers)))

    def test_submit_transfer(self):
        self.step("Create new transfers and wait until the finish")
        transfer = Transfer.api_create(source=self.EXAMPLE_LINK, org=self.org)
        transfer.ensure_finished()
        self.step("Get transfers and check if they are the same as the uploaded ones")
        retrieved_transfer = Transfer.api_get(transfer.id)
        self.assertEqual(transfer, retrieved_transfer, "The transfer is not the same")

    def test_no_token_in_create_transfer_response(self):
        self.step("Create new transfer and check that 'token' field was not returned in response")
        response = api.api_create_transfer(
            source=self.EXAMPLE_LINK,
            title="test-transfer-{}".format(time.time()),
            is_public=False,
            org_guid=self.org.guid
        )
        self.assertTrue("token" not in response, "token field was returned in response")

    def test_create_transfer_with_new_category(self):
        new_category = "user_category"
        self.step("Create a transfer with new category")
        transfer = Transfer.api_create(category=new_category, org=self.org, source=self.EXAMPLE_LINK)
        self.step("Get transfer and check it's category")
        retrieved_transfer = Transfer.api_get(transfer.id)
        self.assertEqual(retrieved_transfer.category, new_category, "Created transfer has different category")


class TransferFromLocalFile(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    def tearDown(self):
        tear_down_test_files()

    def test_create_transfer_from_file(self):
        """DPNG-3156 DAS can't be found by uploader sometimes"""
        self.step("Generate sample csv file")
        file_path = generate_csv_file(column_count=10, row_count=10)
        self.step("Create transfer by uploading a csv file")
        transfer = Transfer.api_create_by_file_upload(self.org, file_path)
        transfer.ensure_finished()
        self.step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer([self.org], transfer.title)

    def test_submit_transfer_from_large_file(self):
        self.step("Generate 20MB csv file")
        file_path = generate_csv_file(size=20*1024*1024)
        self.step("Create transfer by uploading the created file")
        transfer = Transfer.api_create_by_file_upload(self.org, file_path)
        transfer.ensure_finished()
        self.step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer([self.org], transfer.title)

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

import csv
import os
import time
import unittest

from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger, platform_api_calls as api
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

    @unittest.expectedFailure
    def test_cannot_create_transfer_with_incorrect_category(self):
        """DPNG-3035: It's possible to create transfer with unknown category"""
        incorrect_category = "unknown_category"
        self.step("Try to create a transfer with not existing category")
        self.assertRaisesUnexpectedResponse(409, "???", Transfer.api_create, category=incorrect_category, org=self.org,
                                            source=self.EXAMPLE_LINK)


class TransferFromLocalFile(ApiTestCase):

    CSV_FILE_PATH = "test_file.csv"

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        os.remove(cls.CSV_FILE_PATH)

    def _generate_csv_file(self, file_path, column_count, row_count):
        with open(file_path, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["COL_{}".format(i) for i in range(column_count)])
            for i in range(row_count):
                csv_writer.writerow([str(j) * 20 for j in range(column_count)])

    def test_create_transfer_from_file(self):
        """DPNG-3156 DAS can't be found by uploader sometimes"""
        self.step("Generate sample csv file")
        self._generate_csv_file(self.CSV_FILE_PATH, 10, 10)
        self.step("Create transfer by uploading a csv file")
        new_transfer = Transfer.api_create_by_file_upload(self.org, self.CSV_FILE_PATH)
        new_transfer.ensure_finished()
        self.step("Get dataset matching to transfer {}".format(new_transfer.title))
        DataSet.api_get_matching_to_transfer([self.org], new_transfer.title)
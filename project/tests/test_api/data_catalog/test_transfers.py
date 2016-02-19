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
import unittest

from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger, platform_api_calls as api, \
    generate_csv_file, tear_down_test_files, get_test_name
from objects import Organization, Transfer, DataSet, User
from constants.HttpStatus import DataCatalogHttpStatus as HttpStatus

logger = get_logger("test data transfer")


class SubmitTransferBase(ApiTestCase):
    EXAMPLE_LINK = "http://fake-csv-server.gotapaas.eu/fake-csv/2"

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)


class SubmitTransfer(SubmitTransferBase):
    def _create_transfer(self, category):
        self.step("Create new transfers and wait until the finish")
        transfer = Transfer.api_create(category=category, source=self.EXAMPLE_LINK, org=self.org)
        transfer.ensure_finished()
        return transfer

    def test_submit_transfer(self):
        transfer = self._create_transfer(category="other")
        self.step("Get transfers and check if they are the same as the uploaded ones")
        retrieved_transfer = Transfer.api_get(transfer.id)
        self.assertEqual(transfer, retrieved_transfer, "The transfer is not the same")

    def test_create_transfer_with_new_category(self):
        new_category = "user_category"
        transfer = self._create_transfer(category=new_category)
        self.step("Get transfer and check it's category")
        retrieved_transfer = Transfer.api_get(transfer.id)
        self.assertEqual(retrieved_transfer.category, new_category, "Created transfer has different category")

    def test_cannot_create_transfer_when_providing_invalid_org_guid(self):
        org_guid = "wrong_guid"
        self.step("Try create a transfer by providing invalid org guid")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_NOT_VALID_UUID,
                                            api.api_create_transfer, source=self.EXAMPLE_LINK,
                                            title="test-transfer-{}".format(time.time()), is_public=False,
                                            org_guid=org_guid, category="other")

    def test_create_transfer_without_category(self):
        transfer = self._create_transfer(category=None)
        self.step("Get transfer and check it's category")
        transfer_list = Transfer.api_get_list([self.org])
        self.assertInList(transfer, transfer_list, "Transfer was not found")

    def test_no_token_in_create_transfer_response(self):
        self.step("Create new transfer and check that 'token' field was not returned in response")
        response = api.api_create_transfer(
            source=self.EXAMPLE_LINK,
            title=get_test_name(),
            is_public=False,
            org_guid=self.org.guid,
            category="other"
        )
        self.assertTrue("token" not in response, "token field was returned in response")


class SubmitTransferFromLocalFile(SubmitTransfer):
    def _create_transfer(self, column_count=10, row_count=10, category="other", size=None, file_name=None):
        self.step("Generate sample csv file")
        file_path = generate_csv_file(column_count=column_count, row_count=row_count, size=size, file_name=file_name)
        self.step("Create a transfer with new category")
        transfer = Transfer.api_create_by_file_upload(category=category, org=self.org, file_path=file_path)
        transfer.ensure_finished()
        return transfer

    def tearDown(self):
        tear_down_test_files()

    def test_submit_transfer_from_large_file(self):
        transfer = self._create_transfer(size=20 * 1024 * 1024)
        self.step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer([self.org], transfer.title)

    @unittest.expectedFailure
    def test_cannot_create_transfer_when_providing_wrong_org_guid(self):
        """DPNG-3896 Wrong response when trying to create transfer by file upload in non existing org"""
        org_guid = "wrong_guid"
        category = "other"
        self.step("Generate sample csv file")
        file_path = generate_csv_file(column_count=10, row_count=10)
        self.step("Create a transfer")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_ORGANIZATION_NOT_EXIST,
                                            api.api_create_transfer_by_file_upload, source=file_path,
                                            title="test-transfer-{}".format(time.time()), is_public=False,
                                            org_guid=org_guid, category=category)

    @unittest.expectedFailure
    def test_create_transfer_without_category(self):
        """DPNG-3678 Create transfer by file upload without category - http 500"""
        return super(SubmitTransferFromLocalFile, self).test_create_transfer_without_category()

    def test_no_token_in_create_transfer_response(self):
        self.step("Generate sample csv file")
        file_path = generate_csv_file(column_count=10, row_count=10)
        self.step("Create new transfer and check that 'token' field was not returned in response")
        response = api.api_create_transfer_by_file_upload(
            source=file_path,
            title="test-transfer-{}".format(time.time()),
            is_public=False,
            org_guid=self.org.guid,
            category="other"
        )
        self.assertTrue("token" not in response, "token field was returned in response")

    def test_submit_transfer_from_file_with_space_in_name(self):
        transfer = self._create_transfer(file_name="test file with space in name {}.csv")
        self.step("Get data set matching to transfer {}".format(transfer.title))
        DataSet.api_get_matching_to_transfer([self.org], transfer.title)


class OtherTransferTests(SubmitTransferBase):
    def test_admin_can_get_transfer_list(self):
        self.step("Check if the list of transfers can be retrieved")
        transfers = Transfer.api_get_list(org_list=[self.org])
        logger.info("{} transfers".format(len(transfers)))

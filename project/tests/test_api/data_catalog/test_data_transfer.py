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

from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger
from test_utils.objects import Organization, Transfer, DataSet, User
import test_utils.platform_api_calls as api


logger = get_logger("test data transfer")


class TestDataTransfer(ApiTestCase):

    EXAMPLE_LINK = "http://fake-csv-server.gotapaas.eu/fake-csv/2"

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.org = Organization.api_create()
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    def test_get_transfers(self):
        transfers = Transfer.api_get_list(orgs=[self.org])
        logger.info("{} transfers".format(len(transfers)))

    def test_submit_transfer(self):
        expected_transfer = Transfer.api_create(source=self.EXAMPLE_LINK, org_guid=self.org.guid)
        expected_transfer.ensure_finished()
        transfer = Transfer.api_get(expected_transfer.id)
        self.assertAttributesEqual(transfer, expected_transfer)

    def test_match_dataset_to_transfer(self):
        expected_transfer = Transfer.api_create(source=self.EXAMPLE_LINK, org_guid=self.org.guid)
        expected_transfer.ensure_finished()
        transfers = Transfer.api_get_list(orgs=[self.org])
        self.assertInList(expected_transfer, transfers)
        dataset = DataSet.api_get_matching_to_transfer(org_list=[self.org], transfer_title=expected_transfer.title)
        self.assertIsNotNone(dataset, "Dataset matching transfer {} was not found".format(expected_transfer))

    def test_no_token_in_create_transfer_response(self):
        """Verify that the request to create a transfer does not leak 'token' field"""
        response = api.api_create_transfer(
            source=self.EXAMPLE_LINK,
            title="test-transfer-{}".format(time.time()),
            is_public=False,
            org_guid=self.org.guid
        )
        self.assertTrue("token" not in response, "token field was returned in response")


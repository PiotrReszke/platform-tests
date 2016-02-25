#
# Copyright (c) 2016 Intel Corporation
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
from constants.priority_levels import Priority
from test_utils import ApiTestCase, cleanup_after_failed_setup, Arcadia, incremental
from objects import Organization, User, Transfer, DataSet


@incremental(Priority.high)
class ArcadiaTest(ApiTestCase):
    LINK_TO_CSV = "http://fake-csv-server.gotapaas.eu/fake-csv/2"
    arcadia = None

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs, User.cf_api_tear_down_test_users,
                                Transfer.api_teardown_test_transfers, DataSet.api_teardown_test_datasets)
    def setUpClass(cls):
        cls.step("Create test organization and test spaces")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.test_org.guid)
        cls.step("Create non admin user")
        cls.non_admin_client = User.api_create_by_adding_to_space(cls.test_org.guid, cls.test_space.guid).login()
        cls.step("Create new transfer")
        cls.transfer = Transfer.api_create(org=cls.test_org, source=cls.LINK_TO_CSV)
        cls.dataset = DataSet.api_get_matching_to_transfer([cls.test_org], cls.transfer.title)
        cls.step("Get arcadia dataconnection")
        cls.arcadia = Arcadia()

    @classmethod
    def tearDownClass(cls):
        cls.arcadia.teardown_test_datasets()
        super().tearDownClass()

    def test_0_create_new_dataset_and_import_it_to_arcadia(self):
        self.step("Publish created dataset")
        self.dataset.api_publish()
        self.step("Check that organization name is visible on the database list in arcadia")
        db_list = self.arcadia.get_database_list()
        self.assertIn(self.test_org.name, db_list, "Organization not found in database list in arcadia")
        self.step("Check that dataset name is visible on the table list in arcadia")
        table_list = self.arcadia.get_table_list(self.test_org.name)
        self.assertIn(self.dataset.title, table_list, "Dataset not found in table list in arcadia")
        self.step("Create new dataset in arcadia")
        arcadia_dataset = self.arcadia.create_dataset(self.test_org.name, self.dataset.title)
        self.assertInWithRetry(arcadia_dataset, self.arcadia.get_dataset_list)

    def test_1_change_dataset_to_public_and_import_it_to_arcadia(self):
        self.step("Change dataset to public")
        self.dataset.api_update(is_public=True)
        self.dataset = DataSet.api_get(self.dataset.id)
        self.assertTrue(self.dataset.is_public, "Dataset was not updated")
        self.step("Publish updated dataset")
        self.dataset.api_publish()
        self.step("Check that dataset name is visible on the public table list in arcadia")
        table_list = self.arcadia.get_table_list("public")
        self.assertIn(self.dataset.title, table_list, "Dataset not found in table list in arcadia")
        self.step("Create new dataset in arcadia")
        arcadia_dataset = self.arcadia.create_dataset("public", self.dataset.title)
        self.assertInWithRetry(arcadia_dataset, self.arcadia.get_dataset_list)

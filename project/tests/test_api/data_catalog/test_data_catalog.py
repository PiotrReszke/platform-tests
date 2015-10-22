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
from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger
from objects import Organization, Transfer, DataSet, User


logger = get_logger("test data transfer")


class DataCatalog(ApiTestCase):

    EXAMPLE_LINK = "http://fake-csv-server.gotapaas.eu/fake-csv/2"
    CATEGORIES = ["other", "agriculture", "climate", "science", "energy", "business", "consumer", "education",
                  "finance", "manufacturing", "ecosystems", "health"]
    FILE_FORMATS = ["CSV"]

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)
        cls.step("Create new transfer for each category")
        cls.transfers = []
        is_public = True
        for category in cls.CATEGORIES:
            is_public = not is_public
            cls.transfers.append(Transfer.api_create(category, is_public, org=cls.org, source=cls.EXAMPLE_LINK))
        cls.step("Ensure that transfers are finished")
        for transfer in cls.transfers:
            transfer.ensure_finished()
        cls.step("Get datasets list for org {}".format(cls.org))
        cls.datasets = DataSet.api_get_list(org_list=[cls.org])

    def test_match_dataset_to_transfer(self):
        self.step("Check if data set was created for the new transfer")
        missing_ds = []
        dataset_titles = [ds.title for ds in self.datasets]
        for tr in self.transfers:
            if tr.title not in dataset_titles:
                missing_ds.append(tr.title)
        self.assertEqual(missing_ds, [], "Missing datasets: {}".format(missing_ds))

    def test_get_dataset_by_category(self):
        self.step("Retrieve datasets by categories and check if result is same as expected")
        for category in self.CATEGORIES:
            with self.subTest(category=category):
                filtered_datasets = DataSet.api_get_list(org_list=[self.org], filters=({"category": [category]},))
                expected_datasets = [d for d in self.datasets if d.category == category]
                self.assertListEqual(filtered_datasets, expected_datasets,
                                     "Api returned {} for '{}' category - expected {}"
                                     .format(filtered_datasets, category, expected_datasets))

    def test_get_dataset_by_creation_date(self):
        self.step("Sort dataset creation times and retrieve the first two")
        time_range = sorted([dataset.creation_time for dataset in self.datasets][:2])
        self.step("Retrieve datasets for specified range and check correctness of the result")
        filtered_datasets = DataSet.api_get_list(org_list=[self.org], filters=({"creationTime": time_range},))
        expected_datasets = [d for d in self.datasets if time_range[0] <= d.creation_time <= time_range[1]]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets,
                                      "Api returned {} for range ({} - {}) - expected {}"
                                      .format(filtered_datasets, time_range[0], time_range[1], expected_datasets))

    def test_get_dataset_by_file_format(self):
        # Test should be updated when we will receive answer about supported file formats.
        self.step("Retrieve datasets by file format and check correctness of the result")
        for file_format in self.FILE_FORMATS:
            with self.subTest(file_format=file_format):
                filtered_datasets = DataSet.api_get_list(org_list=[self.org], filters=({"format": [file_format]},))
                expected_datasets = [d for d in self.datasets if d.format == file_format]
                self.assertUnorderedListEqual(filtered_datasets, expected_datasets,
                                              "Api returned {} for {} format - expected {}"
                                              .format(filtered_datasets, file_format, expected_datasets))

    def test_get_public_datasets_from_current_org(self):
        self.step("Retrieve public datasets and check correctness of the result")
        filtered_datasets = DataSet.api_get_list(org_list=[self.org], only_public=True)
        expected_datasets = [d for d in self.datasets if d.is_public]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets,
                                      "Api returned {} - expected {}".format(filtered_datasets, expected_datasets))

    def test_get_private_datasets_from_current_org(self):
        self.step("Retrieve private datasets and check correctness of the result")
        filtered_datasets = DataSet.api_get_list(org_list=[self.org], only_private=True)
        expected_datasets = [d for d in self.datasets if not d.is_public]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets,
                                      "Api returned {} - expected {}".format(filtered_datasets, expected_datasets))

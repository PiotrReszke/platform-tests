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
import urllib.request

from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger
from objects import Organization, Transfer, DataSet, User


logger = get_logger("test data transfer")

EXAMPLE_LINK = "http://fake-csv-server.gotapaas.eu/fake-csv/2"
CATEGORIES = ["other", "agriculture", "climate", "science", "energy", "business", "consumer", "education", "finance",
              "manufacturing", "ecosystems", "health"]
FILE_FORMATS = ["CSV"]


class RetrieveDataSetsFromDataCatalog(ApiTestCase):

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
        for category in CATEGORIES:
            is_public = not is_public
            cls.transfers.append(Transfer.api_create(category, is_public, org=cls.org, source=EXAMPLE_LINK))
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
        for category in CATEGORIES:
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
        for file_format in FILE_FORMATS:
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

    def test_get_all_public_datasets_from_other_org(self):
        self.step("Create test organization")
        org = Organization.api_create()
        self.step("Retrieve public datasets for test org")
        public_datasets = [ds for ds in DataSet.api_get_list(org_list=[org], only_public=True)]
        filtered_datasets = [ds for ds in self.datasets if ds.is_public]
        self.step("Check if public datasets from other orgs are visible in test org")
        self.assertUnorderedListEqual(public_datasets, filtered_datasets,
                                      "Public datasets are not visible in test org")

    def test_try_get_private_datasets_from_other_org(self):
        self.step("Create test organization")
        org = Organization.api_create()
        self.step("Retrieve private datasets from {} and check if datasets from different org are visible".format(org))
        datasets_list = [ds for ds in DataSet.api_get_list(org_list=[org])]
        private_ds_list = [ds for ds in datasets_list if not ds.is_public]
        self.assertEqual(len(private_ds_list), 0,
                         "Private datasets from different org were found: {}".format(private_ds_list))

    def test_dataset_details(self):
        self.step("Get transfer and matching dataset")
        transfer = self.transfers[0]
        dataset = next(iter([ds for ds in self.datasets if ds.title == transfer.title]), None)
        self.step("Check that dataset exists for chosen transfer")
        self.assertIsNotNone(dataset, "Dataset doesn't exist for transfer {}".format(transfer))
        self.assertEqual(dataset.category, transfer.category, "Dataset has wrong category: {}".format(dataset.category))
        self.assertEqual(dataset.org_guid, transfer.organization_guid,
                         "Dataset has wrong category: {}".format(dataset.org_guid))
        self.assertInList(dataset.format, FILE_FORMATS, "Dataset has wrong format: {}".format(dataset.format))
        self.assertEqual(dataset.is_public, transfer.is_public,
                         "Dataset has wrong access rights: {}".format(dataset.is_public))
        self.assertEqual(dataset.source_uri, transfer.source,
                         "Dataset has wrong source uri: {}".format(dataset.source_uri))


class ModifyDataSetsInDataCatalog(ApiTestCase):

    def _create_transfer(self, org, source, is_public=False, category=CATEGORIES[0]):
        self.step("Create new transfer")
        new_transfer = Transfer.api_create(org=org, source=source, is_public=is_public, category=category)
        self.step("Wait for transfer to finish")
        new_transfer.ensure_finished()
        return new_transfer

    def _get_dataset_and_update(self, transfer_title, timeout=30, **kwargs):
        self.step("Get dataset matching to transfer '{}'".format(transfer_title))
        dataset = DataSet.api_get_matching_to_transfer([self.org], transfer_title)
        self.step("Update dataset")
        dataset.api_update(**kwargs)
        self.step("Wait for dataset to update")
        start = time.time()
        while time.time() - start < timeout:
            updated_dataset = DataSet.api_get_matching_to_transfer([self.org], transfer_title)
            if dataset != updated_dataset:
                return updated_dataset
            time.sleep(5)
        return

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    def test_delete_dataset(self):
        new_transfer = self._create_transfer(self.org, EXAMPLE_LINK)
        self.step("Get dataset matching to transfer {} and check if its not None".format(new_transfer.title))
        new_dataset = DataSet.api_get_matching_to_transfer([self.org], new_transfer.title)
        self.assertIsNotNone(new_dataset, "Dataset was not retrieved")
        self.step("Delete dataset {}".format(new_dataset.title))
        new_dataset.api_delete()
        self.step("Check if dataset {} was deleted".format(new_dataset.title))
        dataset_list = DataSet.api_get_list(org_list=[self.org])
        self.assertNotInList(new_dataset, dataset_list, "Dataset {} was not deleted.".format(new_dataset))

    def test_try_delete_not_existing_dataset(self):
        new_transfer = self._create_transfer(self.org, EXAMPLE_LINK)
        self.step("Get dataset matching to transfer {}".format(new_transfer.title))
        new_dataset = DataSet.api_get_matching_to_transfer([self.org], new_transfer.title)
        self.step("Delete dataset {}".format(new_dataset.title))
        new_dataset.api_delete()
        self.step("Try to delete not existing dataset {}".format(new_dataset.title))
        self.assertRaisesUnexpectedResponse(404, "null", new_dataset.api_delete)

    def test_change_private_dataset_to_public(self):
        new_transfer = self._create_transfer(self.org, EXAMPLE_LINK, is_public=False)
        updated_dataset = self._get_dataset_and_update(new_transfer.title, is_public=True)
        self.step("Check if private dataset was changed to public")
        self.assertTrue(updated_dataset.is_public, "Dataset was not changed to public.")

    def test_change_public_dataset_to_private(self):
        new_transfer = self._create_transfer(self.org, EXAMPLE_LINK, is_public=True)
        updated_dataset = self._get_dataset_and_update(new_transfer.title, is_public=False)
        self.step("Check if public dataset was changed to private")
        self.assertFalse(updated_dataset.is_public, "Dataset was not changed to private.")

    def test_update_dataset_category(self):
        old_category = CATEGORIES[0]
        new_category = CATEGORIES[1]
        new_transfer = self._create_transfer(self.org, EXAMPLE_LINK, category=old_category)
        updated_dataset = self._get_dataset_and_update(new_transfer.title, category=new_category)
        self.step("Check if dataset category was changed")
        self.assertEqual(updated_dataset.category, new_category, "Dataset category was not updated.")

    @unittest.expectedFailure
    def test_create_dataset_with_unknown_category(self):
        """DPNG-3035: It's possible to create transfer with unknown category"""
        category = "unknown_category"
        self.step("Try to create a transfer with not existing category")
        self.assertRaisesUnexpectedResponse(409, "???", Transfer.api_create, category=category, org=self.org,
                                            source=EXAMPLE_LINK)

    @unittest.expectedFailure
    def test_update_dataset_with_unknown_category(self):
        """DPNG-3036: It's possible to update dataset with unknown category"""
        category = "unknown_category"
        new_transfer = self._create_transfer(self.org, EXAMPLE_LINK)
        new_dataset = DataSet.api_get_matching_to_transfer([self.org], new_transfer.title)
        self.step("Try to update a transfer with not existing category")
        self.assertRaisesUnexpectedResponse(409, "???", new_dataset.api_update, category=category)

    def test_create_dataset_from_file(self):
        """DPNG-3156 DAS can't be found by uploader sometimes"""
        self.step("Download and save example csv file")
        file_name = "file.csv"
        urllib.request.urlretrieve(EXAMPLE_LINK, file_name)
        self.step("Create transfer by uploading a csv file")
        new_transfer = Transfer.api_create_by_file_upload(self.org, file_name)
        new_transfer.ensure_finished()
        self.step("Get dataset matching to transfer {}".format(new_transfer.title))
        new_dataset = DataSet.api_get_matching_to_transfer([self.org], new_transfer.title)
        self.step("Check if dataset was created")
        self.assertIsNotNone(new_dataset, "Dataset {} created by file upload was not found".format(new_transfer.title))

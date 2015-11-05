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
import unittest

from retry import retry

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import Organization, Transfer, DataSet, User


EXAMPLE_LINK = "http://fake-csv-server.gotapaas.eu/fake-csv/2"


class GetDataSets(ApiTestCase):

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
        for category in DataSet.CATEGORIES:
            is_public = not is_public  # half of the transfers will be created as public, half - as private
            cls.transfers.append(Transfer.api_create(category, is_public, org=cls.org, source=EXAMPLE_LINK))
        cls.step("Ensure that transfers are finished")
        for transfer in cls.transfers:
            transfer.ensure_finished()
        cls.step("Get all data sets in the test org")
        cls.datasets = DataSet.api_get_list(org_list=[cls.org])

    def test_match_dataset_to_transfer(self):
        self.step("Check if a data set was created for each transfer")
        missing_ds = []
        dataset_titles = [ds.title for ds in self.datasets]
        for tr in self.transfers:
            if tr.title not in dataset_titles:
                missing_ds.append(tr.title)
        self.assertEqual(missing_ds, [], "Missing datasets: {}".format(missing_ds))

    def test_get_datasets_by_category(self):
        self.step("Retrieve datasets by categories")
        for category in DataSet.CATEGORIES:
            with self.subTest(category=category):
                filtered_datasets = DataSet.api_get_list(org_list=[self.org], filters=({"category": [category]},))
                expected_datasets = [d for d in self.datasets if d.category == category]
                self.assertListEqual(filtered_datasets, expected_datasets)

    def test_get_datasets_by_creation_date(self):
        self.step("Sort datasets by creation time and retrieve first two")
        time_range = sorted([dataset.creation_time for dataset in self.datasets][:2])
        self.step("Retrieve datasets for specified time range")
        filtered_datasets = DataSet.api_get_list(org_list=[self.org], filters=({"creationTime": time_range},))
        expected_datasets = [d for d in self.datasets if time_range[0] <= d.creation_time <= time_range[1]]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    def test_get_datasets_by_file_format(self):
        # Test should be updated when we will receive answer about supported file formats.
        self.step("Retrieve datasets by file format")
        for file_format in DataSet.FILE_FORMATS:
            with self.subTest(file_format=file_format):
                filtered_datasets = DataSet.api_get_list(org_list=[self.org], filters=({"format": [file_format]},))
                expected_datasets = [d for d in self.datasets if d.format == file_format]
                self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    def test_get_public_datasets_from_current_org(self):
        self.step("Retrieve only public datasets")
        filtered_datasets = DataSet.api_get_list(org_list=[self.org], only_public=True)
        expected_datasets = [d for d in self.datasets if d.is_public]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    def test_get_private_datasets_from_current_org(self):
        self.step("Retrieve only private datasets")
        filtered_datasets = DataSet.api_get_list(org_list=[self.org], only_private=True)
        expected_datasets = [d for d in self.datasets if not d.is_public]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    def test_dataset_details(self):
        self.step("Get transfer and matching dataset")
        transfer = self.transfers[0]
        dataset = next(iter([ds for ds in self.datasets if ds.title == transfer.title]), None)
        self.step("Check that dataset exists for chosen transfer")
        self.assertIsNotNone(dataset, "Dataset doesn't exist for transfer {}".format(transfer))
        self.step("Check dataset and transfer category")
        self.assertEqual(dataset.category, transfer.category)
        self.step("Check dataset and transfer org guid")
        self.assertEqual(dataset.org_guid, transfer.organization_guid)
        self.step("Check dataset and transfer file format")
        self.assertEqual(dataset.format, "CSV")
        self.step("Check dataset and transfer public status")
        self.assertEqual(dataset.is_public, transfer.is_public)
        self.step("Check dataset and transfer source uri")
        self.assertEqual(dataset.source_uri, transfer.source)

    def test_get_data_sets_from_another_org(self):
        self.step("Create another test organization")
        org = Organization.api_create()
        self.step("Retrieve public datasets from the new org")
        public_datasets = [ds for ds in self.datasets if ds.is_public]
        private_datasets = [ds for ds in self.datasets if not ds.is_public]
        datasets = [ds for ds in DataSet.api_get_list(org_list=[org])]
        self.step("Check that no private data sets are visible in another org")
        self.found_private_ds = [ds for ds in private_datasets if ds in datasets]
        self.assertUnorderedListEqual(self.found_private_ds, [], "Private datasets from another org returned")
        self.step("Check that all public data sets are visible in another org")
        self.missing_public_ds = [ds for ds in public_datasets if ds not in datasets]
        self.assertUnorderedListEqual(self.missing_public_ds, [], "Not all public data sets from another org returned")


class UpdateDeleteDataSet(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    def _create_dataset(self, org, source, is_public=False, category=DataSet.CATEGORIES[0]):
        self.step("Create new transfer")
        transfer = Transfer.api_create(org=org, source=source, is_public=is_public, category=category)
        self.step("Wait for transfer to finish")
        transfer.ensure_finished()
        self.step("Get data set matching to transfer")
        return DataSet.api_get_matching_to_transfer([self.org], transfer.title)

    @retry(AssertionError, tries=10, delay=3)
    def _get_updated_dataset(self, original_dataset):
        self.step("Wait for data set to update")
        updated_dataset = DataSet.api_get(original_dataset.id)
        if original_dataset == updated_dataset:
            raise AssertionError("Data set was not updated")
        return updated_dataset

    def test_delete_dataset(self):
        dataset = self._create_dataset(self.org, EXAMPLE_LINK)
        self.step("Delete the dataset")
        dataset.api_delete()
        self.step("Get dataset list and check the deleted one is not on it")
        dataset_list = DataSet.api_get_list(org_list=[self.org])
        self.assertNotInList(dataset, dataset_list)

    def test_cannot_delete_not_existing_dataset(self):
        dataset = self._create_dataset(self.org, EXAMPLE_LINK)
        self.step("Delete dataset")
        dataset.api_delete()
        self.step("Try to delete the dataset again")
        self.assertRaisesUnexpectedResponse(404, "null", dataset.api_delete)

    def test_change_private_dataset_to_public(self):
        dataset = self._create_dataset(self.org, EXAMPLE_LINK)
        self.step("Update dataset from private to public")
        dataset.api_update(is_public=True)
        updated_dataset = self._get_updated_dataset(dataset)
        self.step("Check that private dataset was changed to public")
        self.assertTrue(updated_dataset.is_public, "Dataset was not changed to public.")

    def test_change_public_dataset_to_private(self):
        dataset = self._create_dataset(self.org, EXAMPLE_LINK, is_public=True)
        self.step("Update dataset from public to private")
        dataset.api_update(is_public=False)
        updated_dataset = self._get_updated_dataset(dataset)
        self.step("Check that public dataset was changed to private")
        self.assertFalse(updated_dataset.is_public, "Dataset was not changed to private.")

    def test_update_dataset_category(self):
        old_category = DataSet.CATEGORIES[0]
        new_category = DataSet.CATEGORIES[1]
        dataset = self._create_dataset(self.org, EXAMPLE_LINK, category=old_category)
        self.step("Update dataset, change category")
        dataset.api_update(category=new_category)
        updated_dataset = self._get_updated_dataset(dataset)
        self.step("Check if dataset category was changed")
        self.assertEqual(updated_dataset.category, new_category, "Dataset category was not updated.")

    @unittest.expectedFailure
    def test_cannot_update_dataset_to_incorrect_category(self):
        """DPNG-3036: It's possible to update dataset with unknown category"""
        incorrect_category = "unknown_category"
        dataset = self._create_dataset(self.org, EXAMPLE_LINK)
        self.step("Try to update a transfer with not existing category")
        self.assertRaisesUnexpectedResponse(409, "???", dataset.api_update, category=incorrect_category)

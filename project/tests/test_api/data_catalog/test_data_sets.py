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
import os
import datetime
import unittest

from retry import retry

from constants.tap_components import TapComponent as TAP
from test_utils import ApiTestCase, cleanup_after_failed_setup, get_csv_record_count
from test_utils import tear_down_test_files, get_csv_data, download_file, ATKtools, priority, components
from objects import Organization, Transfer, DataSet, User, Application
from constants.HttpStatus import HttpStatus


EXAMPLE_LINK = "http://fake-csv-server.gotapaas.eu/fake-csv/2"


@components(TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
class GetDataSets(ApiTestCase):

    def _filter_datasets(self, org, filters=(), only_private=False, only_public=False):
        ds_list = DataSet.api_get_list(org_list=[org], filters=filters, only_private=only_private,
                                       only_public=only_public)
        return [d for d in ds_list if d in self.datasets]

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
        transfer_titles = [t.title for t in cls.transfers]
        cls.datasets = [d for d in DataSet.api_get_list(org_list=[cls.org]) if d.title in transfer_titles]

    @classmethod
    def tearDownClass(cls):
        tear_down_test_files()
        super().tearDownClass()

    @priority.high
    def test_match_dataset_to_transfer(self):
        self.step("Check if a data set was created for each transfer")
        missing_ds = []
        dataset_titles = [ds.title for ds in self.datasets]
        for tr in self.transfers:
            if tr.title not in dataset_titles:
                missing_ds.append(tr.title)
        self.assertEqual(missing_ds, [], "Missing datasets: {}".format(missing_ds))

    @priority.medium
    def test_get_datasets_by_category(self):
        self.step("Retrieve datasets by categories")
        for category in DataSet.CATEGORIES:
            with self.subTest(category=category):
                filtered_datasets = self._filter_datasets(self.org, ({"category": [category]},))
                expected_datasets = [d for d in self.datasets if d.category == category]
                self.assertListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_get_datasets_by_creation_date(self):
        self.step("Sort datasets by creation time and retrieve first two")
        time_range = sorted([dataset.creation_time for dataset in self.datasets][:2])
        self.step("Retrieve datasets for specified time range")
        filtered_datasets = self._filter_datasets(self.org, ({"creationTime": time_range},))
        expected_datasets = [d for d in self.datasets if time_range[0] <= d.creation_time <= time_range[1]]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_get_datasets_by_file_format(self):
        # Test should be updated when we will receive answer about supported file formats.
        self.step("Retrieve datasets by file format")
        for file_format in DataSet.FILE_FORMATS:
            with self.subTest(file_format=file_format):
                filtered_datasets = self._filter_datasets(self.org, ({"format": [file_format]},))
                expected_datasets = [d for d in self.datasets if d.format == file_format]
                self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_get_public_datasets_from_current_org(self):
        self.step("Retrieve only public datasets")
        filtered_datasets = self._filter_datasets(self.org, only_public=True)
        expected_datasets = [d for d in self.datasets if d.is_public]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_get_private_datasets_from_current_org(self):
        self.step("Retrieve only private datasets")
        filtered_datasets = self._filter_datasets(self.org, only_private=True)
        expected_datasets = [d for d in self.datasets if not d.is_public]
        self.assertUnorderedListEqual(filtered_datasets, expected_datasets)

    @priority.medium
    def test_compare_dataset_details_with_transfer_details(self):
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

    @priority.medium
    def test_get_data_sets_from_another_org(self):
        self.step("Create another test organization")
        org = Organization.api_create()
        self.step("Retrieve datasets from the new org")
        public_datasets = [ds for ds in self.datasets if ds.is_public]
        private_datasets = [ds for ds in self.datasets if not ds.is_public]
        datasets = [ds for ds in DataSet.api_get_list(org_list=[org])]
        self.step("Check that no private data sets are visible in another org")
        self.found_private_ds = [ds for ds in private_datasets if ds in datasets]
        self.assertUnorderedListEqual(self.found_private_ds, [], "Private datasets from another org returned")
        self.step("Check that all public data sets are visible in another org")
        self.missing_public_ds = [ds for ds in public_datasets if ds not in datasets]
        self.assertUnorderedListEqual(self.missing_public_ds, [], "Not all public data sets from another org returned")


@components(TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
class UpdateDeleteDataSet(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)

    def setUp(self):
        self.step("Create new transfer")
        transfer = Transfer.api_create(org=self.org, source=EXAMPLE_LINK, is_public=False, category=DataSet.CATEGORIES[0])
        self.step("Wait for transfer to finish")
        transfer.ensure_finished()
        self.step("Get data set matching to transfer")
        self.dataset = DataSet.api_get_matching_to_transfer([self.org], transfer.title)

    @retry(AssertionError, tries=10, delay=3)
    def _assert_updated(self, data_set_id, updated_attribute_name, expected_value):
        updated_dataset = DataSet.api_get(data_set_id)
        updated_value = getattr(updated_dataset, updated_attribute_name)
        self.assertEqual(updated_value, expected_value, "Data set was not updated")

    @priority.high
    def test_delete_dataset(self):
        self.step("Delete the data set")
        self.dataset.api_delete()
        self.step("Get data set list and check the deleted one is not on it")
        datasets = DataSet.api_get_list(org_list=[self.org])
        self.assertNotIn(self.dataset, datasets)

    @priority.low
    def test_cannot_delete_data_set_twice(self):
        self.step("Delete data set")
        self.dataset.api_delete()
        self.step("Try to delete the dataset again")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, HttpStatus.MSG_EMPTY, self.dataset.api_delete)

    def test_change_private_to_public_to_private(self):
        self.step("Update data set from private to public")
        self.dataset.api_update(is_public=True)
        self.step("Check that private data set was changed to public")
        self._assert_updated(self.dataset.id, "is_public", True)
        self.step("Update data set from public to private")
        self.dataset.api_update(is_public=False)
        self.step("Check that public data set was changed to private")
        self._assert_updated(self.dataset.id, "is_public", False)

    @priority.low
    def test_update_data_set_category(self):
        new_category = next(c for c in DataSet.CATEGORIES if c != self.dataset.category)
        self.step("Update data set, change category")
        self.dataset.api_update(category=new_category)
        self._assert_updated(self.dataset.id, "category", new_category)

    @priority.low
    def test_update_dataset_to_non_existing_category(self):
        new_category = "user_category"
        self.step("Update data set with new category")
        self.dataset.api_update(category=new_category)
        self._assert_updated(self.dataset.id, "category", new_category)


@components(TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
class CreateDatasets(ApiTestCase):
    DETAILS_TO_COMPARE = {"accessibility", "title", "category", "sourceUri", "size", "orgUUID", "targetUri", "format",
                          "dataSample", "isPublic", "creationTime"}
    ACCESSIBILITIES = {True: "PUBLIC", False: "PRIVATE"}
    FROM_FILE = False

    @classmethod
    def _get_source_and_filepath(cls):
        source = EXAMPLE_LINK
        file_path = download_file(source)
        return source, file_path

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.source, cls.file_path = cls._get_source_and_filepath()
        cls.step("Create test organization")
        cls.org = Organization.api_create()
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.org.guid)
        cls.step("Get target uri from hdfs instance")
        _, ref_space = Organization.get_ref_org_and_space()
        hdfs = next(app for app in Application.cf_api_get_list_by_space(ref_space.guid) if "hdfs-downloader" in app.name)
        cls.target_uri = hdfs.cf_api_env()['VCAP_SERVICES']['hdfs'][0]['credentials']['uri'].replace("%{organization}", cls.org.guid)

    @classmethod
    def tearDownClass(cls):
        tear_down_test_files()
        super(CreateDatasets, cls).tearDownClass()

    def _get_expected_dataset_details(self, org_uuid, format, is_public, file_path, transfer, from_file=False):
        return {'accessibility': self.ACCESSIBILITIES[is_public], 'title': transfer.title,
                'category': transfer.category, 'recordCount': get_csv_record_count(file_path),
                'sourceUri': os.path.split(file_path)[1] if from_file else EXAMPLE_LINK,
                'size': os.path.getsize(file_path), 'orgUUID': org_uuid,
                'targetUri': self.target_uri + "{}".format(transfer.id_in_object_store), 'format': format,
                'dataSample': ",".join(get_csv_data(file_path)), 'isPublic': is_public,
                'creationTime': datetime.datetime.utcfromtimestamp(transfer.timestamps["FINISHED"]).strftime(
                    "%Y-%m-%dT%H:%M")}

    def _get_transfer_and_dataset(self, file_source, is_public):
        self.step("Create transfer by providing a csv from url")
        transfer = Transfer.api_create(DataSet.CATEGORIES[0], is_public, self.org, file_source)
        transfer.ensure_finished()
        self.step("Get data set matching to transfer {}".format(transfer.title))
        data_set = DataSet.api_get_matching_to_transfer([self.org], transfer.title)
        return transfer, data_set

    @priority.medium
    def test_create_dataset(self):
        for is_public, access in self.ACCESSIBILITIES.items():
            transfer, dataset = self._get_transfer_and_dataset(EXAMPLE_LINK, is_public)
            self.step("Generate expected dataset summary and get real dataset summary")
            expected_details = self._get_expected_dataset_details(self.org.guid, "CSV", is_public, self.file_path,
                                                                  transfer, from_file=self.FROM_FILE)
            ds_details = dataset.get_details()
            self.step("Compare dataset details with expected values")
            for key in self.DETAILS_TO_COMPARE:
                with self.subTest(accessibility=access, detail=key):
                    self.assertEqual(expected_details[key], ds_details[key])

    @priority.medium
    def test_create_dataset_recordcount(self):
        """DPNG-3656 Wrong record count for csv file in dataset details"""
        label = "recordCount"
        for is_public, access in self.ACCESSIBILITIES.items():
            transfer, dataset = self._get_transfer_and_dataset(EXAMPLE_LINK, is_public)
            with self.subTest(accessibility=access, detail=label):
                self.assertEqual(dataset.record_count, get_csv_record_count(self.file_path))


@components(TAP.data_catalog, TAP.das, TAP.hdfs_downloader, TAP.metadata_parser)
class DataSetFromHdfs(ApiTestCase):
    atk_virtualenv = None
    atk_url = None

    @classmethod
    @cleanup_after_failed_setup(DataSet.api_teardown_test_datasets, Transfer.api_teardown_test_transfers,
                                Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and space")
        cls.org = Organization.api_create(space_names=("test_space", ))
        cls.space = cls.org.spaces[0]
        cls.step("Get reference space")
        _, cls.ref_space = Organization.get_ref_org_and_space()
        cls.step("Add admin to the test space")
        admin_user = User.get_admin()
        admin_user.api_add_to_space(space_guid=cls.space.guid, org_guid=cls.org.guid, roles=("managers", "developers"))
        cls.atk_virtualenv = ATKtools("atk_virtualenv")

    @classmethod
    def tearDownClass(cls):
        cls.atk_virtualenv.teardown(atk_url=cls.atk_url)
        super().tearDownClass()

    def _create_dataset(self, org, source, is_public=False, category=DataSet.CATEGORIES[0]):
        self.step("Create new transfer")
        transfer = Transfer.api_create(org=org, source=source, category=category, is_public=is_public)
        self.step("Wait for transfer to finish")
        transfer.ensure_finished()
        self.step("Get data set matching to transfer")
        return DataSet.api_get_matching_to_transfer([org], transfer.title)

    @priority.medium
    def test_create_dataset_from_hdfs_uri(self):
        self.step("Create source dataset")
        source_dataset = self._create_dataset(self.org, EXAMPLE_LINK)
        self.step("Create dataset from hdfs uri")
        dataset = self._create_dataset(self.org, source_dataset.target_uri)
        self.assertEqual(dataset.source_uri, source_dataset.target_uri)

    @priority.low
    @unittest.skip("We don't know how this should work")
    def test_create_transfer_from_atk_model_file(self):
        model_path = os.path.join("test_utils", "models", "lda.csv")
        test_data_directory = os.path.join("test_utils", "atk_test_scripts")
        self.step("Create transfer")
        initial_transfer = Transfer.api_create_by_file_upload(org=self.org, file_path=model_path)
        initial_transfer.ensure_finished()
        initial_dataset = DataSet.api_get_matching_to_transfer([self.org], initial_transfer.title)
        self.step("Get atk app from seedspace")
        atk_app = next((app for app in Application.cf_api_get_list_by_space(self.ref_space.guid) if app.name == "atk"), None)
        if atk_app is None:
            raise AssertionError("Atk app not found in seedspace")
        self.step("Create virtualenv")
        self.atk_virtualenv.create()
        self.step("Install the atk client package")
        self.atk_virtualenv.pip_install(ATKtools.get_atk_client_url(atk_app.urls[0]))
        self.step("Run atk create model script")
        ATKtools.check_uaac_token()
        atk_test_script_path = os.path.join(test_data_directory, "atk_create_model.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, atk_app.urls[0],
                                                      arguments={"--target_uri": initial_dataset.target_uri})
        self.step("Retrieve path to model file created by atk")
        hdfs_model_path = response.split("hdfs_model_path: ", 1)[1]
        self.step("Create dataset by providing retrieved model file path")
        ds = self._create_dataset(self.org, source=hdfs_model_path)
        self.assertEqual(ds.source_uri, hdfs_model_path)

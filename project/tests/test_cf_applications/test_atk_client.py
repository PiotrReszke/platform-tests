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
import shutil
import tarfile
import time
import unittest

from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup, cloud_foundry as cf, ATKtools
from objects import Organization, Transfer, DataSet, AtkInstance, ServiceType, Application, User


logger = get_logger("test ATK")


class AtkTestException(AssertionError):
    pass

@unittest.skip("Problem with publishing in hive - DPNG-2010")
class TestCreateAtkInstance(ApiTestCase):
    DATA_SOURCE = "http://fake-csv-server.gotapaas.eu/fake-csv/2"
    UAA_FILENAME = "pyclient.test"
    TEST_DATA_DIRECTORY = os.path.join("test_utils", "atk_test_scripts")
    UAA_FILE_PATH = os.path.join(TEST_DATA_DIRECTORY, UAA_FILENAME)
    ATK_SERVICE_LABEL = "atk"
    atk_virtualenv = None
    atk_client_tar_file_path = None
    atk_client_directory = None
    atk_app = None

    def _assert_uaa_file_is_not_empty(self):
        with open(self.UAA_FILE_PATH) as f:
            content = f.read()
        self.assertNotEqual(content, "", "uaa file was not created by atk client")

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        admin_user = User.get_admin()
        cls.test_org = Organization.api_create(space_names=("test_space",))
        admin_user.api_add_to_organization(org_guid=cls.test_org.guid)
        cls.test_space = cls.test_org.spaces[0]
        admin_user.api_add_to_space(space_guid=cls.test_space.guid, org_guid=cls.test_org.guid, roles=("managers",
                                                                                                       "developers"))
        cf.cf_login(cls.test_org.name, cls.test_space.name)

        cls.transfer = Transfer.api_create(source=cls.DATA_SOURCE, org_guid=cls.test_org.guid)
        cls.transfer.ensure_finished()
        transfers = Transfer.api_get_list(orgs=[cls.test_org])
        if cls.transfer not in transfers:
            raise AtkTestException("Transfer {} not submitted properly".format(cls.transfer))
        cls.dataset = DataSet.api_get_matching_to_transfer(org_list=[cls.test_org], transfer_title=cls.transfer.title)
        cls.dataset.publish_in_hive()

        marketplace_services = ServiceType.api_get_list_from_marketplace(cls.test_space.guid)
        atk_service = next((s for s in marketplace_services if s.label == cls.ATK_SERVICE_LABEL), None)
        if atk_service is None:
            raise AtkTestException("No atk service found in marketplace in {}".format(cls.test_space))

        atk_service_instance = AtkInstance.cf_create(cls.test_space.guid, atk_service.guid)
        if atk_service_instance is None:
            raise AtkTestException("Atk instance is not found in {}".format(cls.test_space))
        time.sleep(20)  # ATK application needs time before it appears on application list
        cls.atk_app = Application.ensure_started(space_guid=cls.test_space.guid, application_name_prefix="atk-")
        if cls.atk_app is None:
            raise AtkTestException("ATK application is not on application list")

        atk_client_file_name = ATKtools.api_get_atk_client_file()
        cls.atk_client_tar_file_path = os.path.join(atk_client_file_name)
        with tarfile.open(atk_client_file_name) as tar:
            tar.extractall(path=cls.TEST_DATA_DIRECTORY)
        cls.atk_client_directory = os.path.join(cls.TEST_DATA_DIRECTORY, atk_client_file_name.split(".tar")[0])

        cls.atk_virtualenv = ATKtools("atk_virtualenv")
        cls.atk_virtualenv.create()
        cls.atk_virtualenv.pip_install_local_package(cls.atk_client_directory)

    @classmethod
    def tearDownClass(cls):
        if cls.atk_app is not None:
            atk_test_script_path = os.path.join(cls.TEST_DATA_DIRECTORY, "remove_test_tables.py")
            ATKtools.hive_clean_up(cls.atk_virtualenv, atk_test_script_path, cls.atk_app.urls[0], cls.UAA_FILENAME)
        if os.path.exists(cls.UAA_FILE_PATH):
            os.remove(cls.UAA_FILE_PATH)
        if cls.atk_virtualenv is not None:
            cls.atk_virtualenv.delete()
        if cls.atk_client_tar_file_path is not None and os.path.exists(cls.atk_client_tar_file_path):
            os.remove(cls.atk_client_tar_file_path)
        if cls.atk_client_directory is not None and os.path.exists(cls.atk_client_directory):
            shutil.rmtree(cls.atk_client_directory)
        Organization.cf_api_tear_down_test_orgs()

    def test_atk_client_connection(self):
        atk_test_script_path = os.path.join(self.TEST_DATA_DIRECTORY, "atk_client_connection_test.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_app.urls[0],
                                                      arguments={
                                                          "--organization": self.test_org.name,
                                                          "--transfer": self.transfer.title,
                                                          "--uaa_file_name": self.UAA_FILENAME})
        self.assertNotIn("Traceback", response, msg=response.split("Traceback", 1)[1])
        self._assert_uaa_file_is_not_empty()

    @unittest.expectedFailure
    def test_csv_file(self):
        """DPNG-2108 Dataset targetUri shows wrong hdfs path and DPNG-2106 Datasets published in Hue are empty"""
        atk_test_script_path = os.path.join(self.TEST_DATA_DIRECTORY, "csv_file_test.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_app.urls[0],
                                                      arguments={
                                                          "--organization": self.test_org.name,
                                                          "--transfer": self.transfer.title,
                                                          "--uaa_file_name": self.UAA_FILENAME,
                                                          "--target_uri": self.dataset.target_uri})
        self.assertNotIn("Traceback", response, msg=response.split("Traceback", 1)[1])
        self._assert_uaa_file_is_not_empty()

    def test_export_to_hive(self):
        atk_test_script_path = os.path.join(self.TEST_DATA_DIRECTORY, "export_to_hive_test.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_app.urls[0],
                                                      arguments={
                                                          "--organization": self.test_org.name,
                                                          "--transfer": self.transfer.title,
                                                          "--uaa_file_name": self.UAA_FILENAME})
        self.assertNotIn("Traceback", response, msg=response.split("Traceback", 1)[1])
        self._assert_uaa_file_is_not_empty()

    @unittest.expectedFailure
    def test_table_manipulation(self):
        """DPNG-2199 ATK client cannot add column to frame and DPNG-2324 ATK client cannot drop frames in one request"""
        atk_test_script_path = os.path.join(self.TEST_DATA_DIRECTORY, "table_manipulation_test.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_app.urls[0],
                                                      arguments={
                                                          "--organization": self.test_org.name,
                                                          "--transfer": self.transfer.title,
                                                          "--uaa_file_name": self.UAA_FILENAME})
        self.assertNotIn("Traceback", response, msg=response.split("Traceback", 1)[1])
        self._assert_uaa_file_is_not_empty()

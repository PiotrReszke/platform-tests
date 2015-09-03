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

from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup, cloud_foundry as cf, ATKtools
from objects import Organization, Transfer, DataSet, AtkInstance, ServiceType, Application, User


logger = get_logger("test ATK")


class TestCreateAtkInstance(ApiTestCase):

    DATA_SOURCE = "http://fake-csv-server.gotapaas.eu/fake-csv/2"
    UAA_FILENAME = "pyclient.test"
    TEST_DATA_DIRECTORY = os.path.join("tests", "atk_test_scripts")
    UAA_FILE_PATH = os.path.join(TEST_DATA_DIRECTORY, UAA_FILENAME)
    ATK_TEST_SCRIPT_PATH = os.path.join(TEST_DATA_DIRECTORY, "atk_python_client_test.py")
    ATK_SERVICE_LABEL = "atk"

    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUp(self):
        admin_user = User.get_admin()
        self.test_org = Organization.api_create(space_names=("test_space",))
        admin_user.api_add_to_organization(org_guid=self.test_org.guid)
        self.test_space = self.test_org.spaces[0]
        admin_user.api_add_to_space(space_guid=self.test_space.guid, org_guid=self.test_org.guid, roles=("managers",
                                                                                                         "developers"))
        cf.cf_login(self.test_org.name, self.test_space.name)
        self.atk_virtualenv = self.atk_client_tar_file_path = self.atk_client_directory = None

    def tearDown(self):
        if os.path.exists(self.UAA_FILE_PATH):
            os.remove(self.UAA_FILE_PATH)
        if self.atk_virtualenv is not None:
            self.atk_virtualenv.delete()
        if self.atk_client_tar_file_path is not None and os.path.exists(self.atk_client_tar_file_path):
            os.remove(self.atk_client_tar_file_path)
        if self.atk_client_directory is not None and os.path.exists(self.atk_client_directory):
            shutil.rmtree(self.atk_client_directory)
        Organization.cf_api_tear_down_test_orgs()

    def test_create_atk_instance(self):

        transfer = Transfer.api_create(source=self.DATA_SOURCE, org_guid=self.test_org.guid)
        transfer.ensure_finished()
        transfers = Transfer.api_get_list(orgs=[self.test_org])
        self.assertInList(transfer, transfers)
        dataset = DataSet.api_get_matching_to_transfer(org_list=[self.test_org], transfer_title=transfer.title)
        dataset.publish_in_hive()

        marketplace_services = ServiceType.api_get_list_from_marketplace(self.test_space.guid)
        atk_service = next((s for s in marketplace_services if s.label == self.ATK_SERVICE_LABEL), None)
        self.assertIsNotNone(atk_service, "No atk service found in marketplace in {}".format(self.test_space))

        atk_service_instance = AtkInstance.cf_create(self.test_space.guid, atk_service.guid)
        self.assertIsNotNone(atk_service_instance, "Atk instance is not found in {}".format(self.test_space))
        time.sleep(20)  # ATK application needs time before it appears on application list
        atk_app = Application.ensure_started(space_guid=self.test_space.guid, application_name_prefix="atk-", timeout=840)
        self.assertIsNotNone(atk_app, "atk application is not on application list")

        atk_client_file_name = ATKtools.api_get_atk_client_file()
        self.atk_client_tar_file_path = os.path.join(atk_client_file_name)
        with tarfile.open(atk_client_file_name) as tar:
            tar.extractall(path=self.TEST_DATA_DIRECTORY)
        self.atk_client_directory = os.path.join(self.TEST_DATA_DIRECTORY, atk_client_file_name.split(".tar")[0])

        self.atk_virtualenv = ATKtools("atk_virtualenv")
        self.atk_virtualenv.create()
        self.atk_virtualenv.pip_install_local_package(self.atk_client_directory)
        self.atk_virtualenv.run_atk_script(self.ATK_TEST_SCRIPT_PATH, atk_app.urls[0],
                                           arguments={
                                               "--organization": self.test_org.name,
                                               "--transfer": transfer.title,
                                               "--uaa_file_name": self.UAA_FILENAME
                                           })

        with open(self.UAA_FILE_PATH) as f:
            content = f.read()
        self.assertNotEqual(content, "", "uaa file was not created by atk client")


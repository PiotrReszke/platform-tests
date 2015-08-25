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

from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup
from test_utils.objects import Organization, Transfer, DataSet, AtkInstance, ServiceType, Application
from test_utils.cli.atk_tools import ATKtools
import test_utils.cli.cloud_foundry as cf

logger = get_logger("test ATK")


class TestCreateAtkInstance(ApiTestCase):

    DATA_SOURCE = Transfer.get_test_transfer_link()
    UAA_FILENAME = "pyclient.test"
    TEST_DATA_DIRECTORY = os.path.join("tests", "atk_test_scripts")
    UAA_FILE_PATH = os.path.join(TEST_DATA_DIRECTORY, UAA_FILENAME)
    ATK_TEST_SCRIPT_PATH = os.path.join(TEST_DATA_DIRECTORY, "atk_python_client_test.py")
    ATK_SERVICE_LABEL = "atk"

    @cleanup_after_failed_setup(Organization.api_delete_test_orgs)
    def setUp(self):
        self.test_org = Organization.create(space_names=("test_space",))
        self.test_org.add_admin()
        self.test_space = self.test_org.spaces[0]
        self.test_space.add_admin(self.test_org.guid)
        cf.cf_login(self.test_org.name, self.test_space.name)
        self.atk_virtualenv = self.atk_client_tar_file = self.atk_client_directory = None

    def tearDown(self):
        Organization.api_delete_test_orgs()
        if os.path.exists(self.UAA_FILE_PATH):
            os.remove(self.UAA_FILE_PATH)
        if self.atk_virtualenv is not None:
            self.atk_virtualenv.delete()
        if self.atk_client_tar_file is not None and os.path.exists(self.atk_client_tar_file):
            os.remove(self.atk_client_tar_file)
        if self.atk_client_directory is not None and os.path.exists(self.atk_client_directory):
            shutil.rmtree(self.atk_client_directory)

    def test_create_atk_instance(self):

        transfer = Transfer.api_create(source=self.DATA_SOURCE, org_guid=self.test_org.guid)
        transfer.ensure_finished()
        transfers = Transfer.api_get_list(orgs=[self.test_org])
        self.assertInList(transfer, transfers)
        dataset = DataSet.api_get_matching_to_transfer(org_list=[self.test_org], transfer=transfer)
        dataset.publish_in_hive()

        marketplace_services = ServiceType.api_get_list_from_marketplace(self.test_space.guid)
        atk_service = next((s for s in marketplace_services if s.label == self.ATK_SERVICE_LABEL), None)
        self.assertIsNotNone(atk_service, "No atk service found in marketplace in {}".format(self.test_space))

        atk_service_instance = AtkInstance.cf_create(self.test_space.guid, atk_service.guid)
        self.assertIsNotNone(atk_service_instance, "Atk instance is not found in {}".format(self.test_space))
        test_space_apps = Application.api_get_list(space_guid=self.test_space.guid)
        atk_app = next((app for app in test_space_apps if app.name.startswith("atk-")), None)
        self.assertIsNotNone(atk_app, "atk application is not on application list")

        atk_client_gz_name = ATKtools.api_get_atkfilename()
        self.atk_client_tar_file = os.path.join(atk_client_gz_name)
        ATKtools.api_download(atk_client_gz_name)
        with tarfile.open(atk_client_gz_name) as tar:
            tar.extractall(path=self.TEST_DATA_DIRECTORY)
        atk_client_name = atk_client_gz_name.split(".tar", 1)[0]
        self.atk_client_directory = os.path.join(self.TEST_DATA_DIRECTORY, atk_client_name)

        self.atk_virtualenv = ATKtools("atk_virtualenv")
        self.atk_virtualenv.create()
        self.atk_virtualenv.pip_install_local_package(self.atk_client_directory)
        self.atk_virtualenv.run_atk_script(self.ATK_TEST_SCRIPT_PATH,
                                           arguments={
                                               "--organization": self.test_org.name,
                                               "--atk": atk_app.urls[0],
                                               "--transfer": transfer.title,
                                               "--uaa_file_name": self.UAA_FILENAME
                                           })

        with open(self.UAA_FILE_PATH) as f:
            content = f.read()
        self.assertNotEqual(content, "", "uaa file was not created by atk client")


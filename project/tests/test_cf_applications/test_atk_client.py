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

from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup, cloud_foundry as cf, ATKtools,\
    UnexpectedResponseError, get_test_name
from objects import Organization, Transfer, DataSet, ServiceType, ServiceInstance, Application, User


logger = get_logger("test ATK")


class Atk(ApiTestCase):
    DATA_SOURCE = "http://fake-csv-server.gotapaas.eu/fake-csv/2"
    UAA_FILENAME = "pyclient.test"
    TEST_DATA_DIRECTORY = os.path.join("test_utils", "atk_test_scripts")
    UAA_FILE_PATH = os.path.join(TEST_DATA_DIRECTORY, UAA_FILENAME)
    ATK_SERVICE_LABEL = "atk"
    atk_virtualenv = None
    atk_app = None
    transfer_title = get_test_name()
    dataset = None

    def _assert_uaa_file_is_not_empty(self):
        with open(self.UAA_FILE_PATH) as f:
            content = f.read()
        self.assertNotEqual(content, "", "uaa file was not created by atk client")

    def _create_service_instance(self, org_guid, space_guid, service_label, plan_name, atk_name):
        """
        Create service instance. Return the instance.
        This method was created as creating ATK exceeds server timeout and console returns 504 Gateway Timeout.
        """
        instance_name = atk_name
        return ServiceInstance.api_create(
            org_guid=org_guid,
            space_guid=space_guid,
            service_label=service_label,
            name=instance_name,
            service_plan_name=plan_name
        )

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create(space_names=("test_space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Add admin to the test space")
        admin_user = User.get_admin()
        admin_user.api_add_to_space(space_guid=cls.test_space.guid, org_guid=cls.test_org.guid, roles=("managers",
                                                                                                       "developers"))

    @classmethod
    def tearDownClass(cls):
        if cls.atk_app is not None:
            atk_test_script_path = os.path.join(cls.TEST_DATA_DIRECTORY, "remove_test_tables.py")
            ATKtools.hive_clean_up(cls.atk_virtualenv, atk_test_script_path, cls.atk_app.urls[0], cls.UAA_FILENAME)
        if os.path.exists(cls.UAA_FILE_PATH):
            os.remove(cls.UAA_FILE_PATH)
        if cls.atk_virtualenv is not None:
            cls.atk_virtualenv.delete()
        Organization.cf_api_tear_down_test_orgs()

    @ApiTestCase.mark_prerequisite(is_first=True)
    def test_step1_check_uaac_atk(self):
        self.step("Check if atk-client has correct credentials and is able to download token")
        ATKtools.check_uaac_token()

    @ApiTestCase.mark_prerequisite()
    def test_step2_create_atk_instance(self):
        self.step("Create atk service instance")
        name = get_test_name()
        marketplace_services = ServiceType.api_get_list_from_marketplace(self.test_space.guid)
        atk_service = next((s for s in marketplace_services if s.label == self.ATK_SERVICE_LABEL), None)
        self.assertIsNotNone(atk_service, msg="No atk service found in marketplace in {}".format(self.test_space))
        atk_service_instance = self._create_service_instance(self.test_org.guid, self.test_space.guid,
                                                             self.ATK_SERVICE_LABEL, plan_name="Simple", atk_name=name)
        self.assertIsNotNone(atk_service_instance, msg="Atk instance is not found in {}".format(self.test_space))
        self.step("With huge timeout, check that atk application is created")
        self.__class__.atk_app = Application.ensure_started(space_guid=self.test_space.guid, application_name_prefix=name)
        self.assertIsNotNone(self.atk_app, msg="ATK application is not on application list")

    @ApiTestCase.mark_prerequisite()
    def test_step3_create_dataset_and_publish_it_in_hive(self):
        self.step("Create transfer and check it's finished")
        Transfer.api_create(source=self.DATA_SOURCE, org=self.test_org, title=self.transfer_title).ensure_finished()
        self.step("Publish in hive the data set created based on the submitted transfer")
        self.__class__.dataset = DataSet.api_get_matching_to_transfer(org_list=[self.test_org],
                                                                      transfer_title=self.transfer_title)
        self.dataset.publish_in_hive()

    @ApiTestCase.mark_prerequisite()
    def test_step4_create_virtualenv_for_atk(self):
        self.step("Create virtualenv")
        self.__class__.atk_virtualenv = ATKtools("atk_virtualenv")
        self.atk_virtualenv.create()
        self.step("Install the atk client package")
        self.atk_virtualenv.pip_install_from_url(self.atk_app.urls[0])

    @ApiTestCase.mark_prerequisite()
    def test_step5_atk_client_connection(self):
        self.step("Run atk connection test")
        atk_test_script_path = os.path.join(self.TEST_DATA_DIRECTORY, "atk_client_connection_test.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_app.urls[0],
                                                      arguments={
                                                          "--organization": self.test_org.name,
                                                          "--transfer": self.transfer_title,
                                                          "--uaa_file_name": self.UAA_FILENAME}
                                                      )
        self.assertNotIn("Traceback", response, msg=response)
        self._assert_uaa_file_is_not_empty()

    @ApiTestCase.mark_prerequisite()
    def test_step6_csv_file(self):
        self.step("Run atk csvfile test")
        atk_test_script_path = os.path.join(self.TEST_DATA_DIRECTORY, "csv_file_test.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_app.urls[0],
                                                      arguments={
                                                          "--organization": self.test_org.name,
                                                          "--transfer": self.transfer_title,
                                                          "--uaa_file_name": self.UAA_FILENAME,
                                                          "--target_uri": self.dataset.target_uri}
                                                      )
        self.assertNotIn("Traceback", response, msg=response)
        self._assert_uaa_file_is_not_empty()

    @ApiTestCase.mark_prerequisite()
    def test_step7_export_to_hive(self):
        self.step("Run atk export to hive test")
        atk_test_script_path = os.path.join(self.TEST_DATA_DIRECTORY, "export_to_hive_test.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_app.urls[0],
                                                      arguments={
                                                          "--organization": self.test_org.name,
                                                          "--transfer": self.transfer_title,
                                                          "--uaa_file_name": self.UAA_FILENAME}
                                                      )
        self.assertNotIn("Traceback", response, msg=response)
        self._assert_uaa_file_is_not_empty()

    @ApiTestCase.mark_prerequisite()
    def test_step8_table_manipulation(self):
        self.step("Run atk test")
        atk_test_script_path = os.path.join(self.TEST_DATA_DIRECTORY, "table_manipulation_test.py")
        response = self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_app.urls[0],
                                                      arguments={
                                                          "--organization": self.test_org.name,
                                                          "--transfer": self.transfer_title,
                                                          "--uaa_file_name": self.UAA_FILENAME}
                                                      )
        self.assertNotIn("Traceback", response, msg=response)
        self._assert_uaa_file_is_not_empty()

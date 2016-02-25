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

from constants.priority_levels import Priority
from test_utils import ApiTestCase, cleanup_after_failed_setup, ATKtools, get_test_name, incremental, priority
from objects import Organization, Transfer, DataSet, ServiceType, ServiceInstance, Application, User


@incremental(Priority.high)
class Atk(ApiTestCase):
    DATA_SOURCE = "http://fake-csv-server.gotapaas.eu/fake-csv/2"
    ATK_SERVICE_LABEL = "atk"
    ATK_PLAN_NAME = "Simple"
    atk_virtualenv = None
    atk_url = None
    data_set_hdfs_path = None

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create(space_names=("test_space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Add admin to the test space")
        admin_user = User.get_admin()
        admin_user.api_add_to_space(space_guid=cls.test_space.guid, org_guid=cls.test_org.guid,
                                    roles=User.SPACE_ROLES["developer"])
        cls.step("Create virtualenv for atk client")
        cls.atk_virtualenv = ATKtools("atk_virtualenv")
        cls.atk_virtualenv.create()
        cls.transfer_title = get_test_name()

    @classmethod
    def tearDownClass(cls):
        cls.atk_virtualenv.teardown(atk_url=cls.atk_url)
        super().tearDownClass()

    def test_0_check_atk_uaac_credentials(self):
        self.step("Check if atk has correct credentials and is able to download uaac token")
        ATKtools.check_uaac_token()

    def test_1_create_atk_instance(self):
        self.step("Check that atk service is available in Marketplace")
        marketplace = ServiceType.api_get_list_from_marketplace(self.test_space.guid)
        atk_service = next((s for s in marketplace if s.label == self.ATK_SERVICE_LABEL), None)
        self.assertIsNotNone(atk_service, msg="No atk service found in marketplace.")
        self.step("Create atk service instance")
        atk_instance_name = get_test_name()
        atk_instance = ServiceInstance.api_create(
            org_guid=self.test_org.guid,
            space_guid=self.test_space.guid,
            service_label=self.ATK_SERVICE_LABEL,
            name=atk_instance_name,
            service_plan_name=self.ATK_PLAN_NAME
        )
        self.step("Check that atk instance has been created")
        instances = ServiceInstance.api_get_list(space_guid=self.test_space.guid, service_type_guid=atk_service.guid)
        self.assertIn(atk_instance, instances)
        self.step("Check that atk application is created and started")
        atk_app = self.get_from_list_by_attribute_with_retry(
            attr_name="name",
            attr_value=ATKtools.get_expected_atk_app_name(atk_instance),
            get_list_method=Application.api_get_list,
            space_guid=self.test_space.guid
        )
        atk_app.ensure_started()
        self.__class__.atk_url = atk_app.urls[0]

    def test_2_install_atk_client(self):
        self.step("Install atk client package")
        self.atk_virtualenv.pip_install(ATKtools.get_atk_client_url(self.atk_url))

    def test_3_check_atk_client_connection(self):
        self.step("Run atk connection test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "atk_client_connection_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url)

    def test_4_create_data_set_and_publish_it_in_hive(self):
        """DPNG-2010 Cannot get JDBC connection when publishing dataset to Hive"""
        self.step("Create transfer and check it's finished")
        Transfer.api_create(source=self.DATA_SOURCE, org=self.test_org, title=self.transfer_title).ensure_finished()
        self.step("Publish in hive the data set created based on the submitted transfer")
        data_set = DataSet.api_get_matching_to_transfer(org_list=[self.test_org], transfer_title=self.transfer_title)
        data_set.api_publish()
        self.__class__.data_set_hdfs_path = data_set.target_uri

    def test_5_frame_csv_file(self):
        """kerberos: DPNG-4525, non-kerberos: DPNG-5171"""
        self.step("Run atk csv file test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "csv_file_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--target_uri": self.data_set_hdfs_path})

    def test_6_simple_hive_query(self):
        self.step("Run atk connection test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_simple_query_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--organization": self.test_org.name,
                                                      "--transfer": self.transfer_title})

    def test_7_export_to_hive(self):
        self.step("Run atk export to hive test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_export_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--organization": self.test_org.name,
                                                      "--transfer": self.transfer_title})

    def test_8_hive_table_manipulation(self):
        self.step("Run atk table manipulation test")
        atk_test_script_path = os.path.join(ATKtools.TEST_SCRIPTS_DIRECTORY, "hive_table_manipulation_test.py")
        self.atk_virtualenv.run_atk_script(atk_test_script_path, self.atk_url,
                                           arguments={"--organization": self.test_org.name,
                                                      "--transfer": self.transfer_title})

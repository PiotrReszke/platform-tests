#
# Copyright (c) 2016 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from test_utils import ApiTestCase, get_logger, download_file, Gearpump
from objects import Organization, ServiceInstance


logger = get_logger("test Gearpump")


class GearpumpConsole(ApiTestCase):
    COMPLEXDAG_APP_URL = "https://repo.gotapaas.eu/files/complexdag-2.11.5-0.7.1-SNAPSHOT-assembly.jar"
    COMPLEXDAG_APP_NAME = "dag"
    ONE_WORKER_PLAN_NAME = "1 worker"

    @classmethod
    def setUpClass(cls):
        cls.step("Download file complexdag")
        cls.complexdag_app_path = download_file(url=cls.COMPLEXDAG_APP_URL,
                                                save_file_name="complexdag-2.11.5-0.7.1-SNAPSHOT-assembly.jar")
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Create gearpump instance with plan: 1 worker")
        cls.gearpump = Gearpump(cls.test_org.guid, cls.test_space.guid, service_plan_name=cls.ONE_WORKER_PLAN_NAME)
        cls._assert_gearpump_instance_created(gearpump_data_science=cls.gearpump.data_science,
                                              space_guid=cls.test_space.guid)
        cls.step("Log into gearpump UI")
        cls.gearpump.login()

    @classmethod
    def _assert_gearpump_instance_created(cls, gearpump_data_science, space_guid):
        cls.step("Check that gearpump instance has been created")
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        if gearpump_data_science.instance not in instances:
            raise AssertionError("gearpump instance is not on list of instances")
        gearpump_data_science.get_credentials()

    def test_submit_complexdag_app_to_gearpump_dashboard(self):
        self.step("Submit application complexdag to gearpump dashboard")
        dag_app = self.gearpump.submit_application_jar(self.complexdag_app_path, self.COMPLEXDAG_APP_NAME)
        self.step("Check that submitted application is started")
        self.assertTrue(dag_app.is_started)
        self.step("Kill application")
        dag_app.kill_application()
        self.step("Check that killed application is stopped")
        self.assertFalse(dag_app.is_started)

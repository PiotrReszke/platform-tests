#
# Copyright (c) 2016 Intel Corporation
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

from test_utils import ApiTestCase, cleanup_after_failed_setup, AppClient, download_file, get_test_name
from objects import Organization, ServiceInstance, ServiceInstanceKey, Transfer, DataSet


@unittest.skip("Freezes on intel-data-kerberos-second")
class TestScoringEngineInstance(ApiTestCase):
    MODEL_FILE_NAME = "model.tar"
    MODEL_URL = "https://repo.gotapaas.eu/files/models_a8ab76353c2143509514da386d32a2f8.tar"
    MODEL_FILE_TITLE = "test_model_file"

    @classmethod
    def _create_transfer(cls, org, model_file, category="other"):
        hdfs_client = AppClient.get_admin_client(client_type="app")
        cls.step("Create a transfer")
        transfer = Transfer.api_create_by_file_upload(category=category, org=org, file_path=model_file,
                                                      title=cls.MODEL_FILE_TITLE, client=hdfs_client)
        transfer.ensure_finished()
        return transfer

    @classmethod
    def _create_instance(cls, service_label, plan_name, test_org, test_space, model_file_hdfs_path):
        cls.step("Create test service instance")
        instance_name = get_test_name()
        return ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=service_label,
            name=instance_name,
            service_plan_name=plan_name,
            params={"TAR_ARCHIVE": model_file_hdfs_path}
        )

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test spaces")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Download model file")
        model_file_path = download_file(cls.MODEL_URL, cls.MODEL_FILE_NAME)
        cls.se_label = "scoring-engine"
        cls.se_plan = "Simple"
        cls.step("Upload model file and get hdfs path")
        t = cls._create_transfer(cls.test_org, model_file_path)
        ds = DataSet.api_get_matching_to_transfer([cls.test_org], t.title)
        cls.hdfs_path = ds.target_uri

    def test_create_and_delete_scoring_engine_service_instance(self):
        se_instance = self._create_instance(self.se_label, self.se_plan, self.test_org, self.test_space, self.hdfs_path)
        instances_list = ServiceInstance.api_get_list(self.test_space.guid)
        self.assertInList(se_instance, instances_list, "Scoring-engine was not created")
        self.step("Delete scoring engine instance and check it does not show on the list")
        se_instance.api_delete()
        instances = ServiceInstance.api_get_list(space_guid=self.test_space.guid)
        self.assertNotInList(se_instance, instances, "Scoring engine instance was not deleted")

    def test_create_scoring_engine_service_instance_key(self):
        se_instance = self._create_instance(self.se_label, self.se_plan, self.test_org, self.test_space, self.hdfs_path)
        self.step("Check that the instance exists in summary and has no keys")
        summary = ServiceInstance.api_get_keys(self.test_space.guid)
        self.assertIn(se_instance, summary, "Instance not found in summary")
        self.assertEqual(summary[se_instance], [], "There are keys for the instance")
        self.step("Create a key for the instance and check it")
        instance_key = ServiceInstanceKey.cf_api_create(se_instance.guid)
        summary = ServiceInstance.api_get_keys(self.test_space.guid)
        self.assertInList(instance_key, summary[se_instance], "Key not found")

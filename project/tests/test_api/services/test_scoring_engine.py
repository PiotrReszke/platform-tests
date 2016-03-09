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
from test_utils import ApiTestCase, cleanup_after_failed_setup, priority
from constants.services import ServiceLabels
from objects import Organization, ServiceInstance, ServiceKey, Transfer, DataSet, User


class TestScoringEngineInstance(ApiTestCase):
    MODEL_URL = "https://repo.gotapaas.eu/files/models_a8ab76353c2143509514da386d32a2f8.tar"
    SE_PLAN_NAME = "Simple"

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test spaces")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Add admin to the organization")
        User.get_admin().api_add_to_organization(org_guid=cls.test_org.guid)
        cls.step("Create a transfer and get hdfs path")
        transfer = Transfer.api_create(category="other", org=cls.test_org, source=cls.MODEL_URL)
        transfer.ensure_finished()
        ds = DataSet.api_get_matching_to_transfer([cls.test_org], transfer.title)
        cls.hdfs_path = ds.target_uri

    @priority.high
    def test_create_and_delete_scoring_engine_service_instance(self):
        """DPNG-5389 User cannot create scoring-engine instance (permission denied for user vcap)"""
        self.step("Create test service instance")
        se_instance = ServiceInstance.api_create(
            org_guid=self.test_org.guid,
            space_guid=self.test_space.guid,
            service_label=ServiceLabels.SCORING_ENGINE,
            service_plan_name=self.SE_PLAN_NAME,
            params={"TAR_ARCHIVE": self.hdfs_path}
        )
        instances_list = ServiceInstance.api_get_list(self.test_space.guid)
        self.assertIn(se_instance, instances_list, "Scoring-engine was not created")
        self.step("Delete scoring engine instance and check it does not show on the list")
        se_instance.api_delete()
        instances = ServiceInstance.api_get_list(space_guid=self.test_space.guid)
        self.assertNotIn(se_instance, instances, "Scoring engine instance was not deleted")

    @priority.medium
    def test_create_scoring_engine_service_key(self):
        """DPNG-5389 User cannot create scoring-engine instance (permission denied for user vcap)"""
        self.step("Create test service instance")
        se_instance = ServiceInstance.api_create(
            org_guid=self.test_org.guid,
            space_guid=self.test_space.guid,
            service_label=ServiceLabels.SCORING_ENGINE,
            service_plan_name=self.SE_PLAN_NAME,
            params={"TAR_ARCHIVE": self.hdfs_path}
        )
        self.step("Check that the instance exists in summary and has no keys")
        summary = ServiceInstance.api_get_keys(self.test_space.guid)
        self.assertIn(se_instance, summary, "Instance not found in summary")
        self.assertEqual(summary[se_instance], [], "There are keys for the instance")
        self.step("Create a key for the instance and check it")
        instance_key = ServiceKey.api_create(se_instance.guid)
        summary = ServiceInstance.api_get_keys(self.test_space.guid)
        self.assertIn(instance_key, summary[se_instance], "Key not found")

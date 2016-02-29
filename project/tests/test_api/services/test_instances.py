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

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import Organization, ServiceType, ServiceInstance, ServiceInstanceKey


class ServiceInstanceKeys(ApiTestCase):
    SERVICES_TESTED_SEPARATELY = ['yarn', 'hdfs', 'hbase', "scoring-engine", "gearpump-dashboard"]

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test spaces")
        cls.test_org = Organization.api_create(space_names=("test-space", "test_space_a", "test_space_b"))
        cls.step("Get list of available services from Marketplace")
        cls.marketplace_services = ServiceType.api_get_list_from_marketplace(cls.test_org.spaces[0].guid)

    def _create_instance_and_key(self, service_label, plan_guid, test_org, test_space):
        self.step("Create test service instance")
        instance = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=service_label,
            service_plan_guid=plan_guid
        )
        self.step("Check that the instance exists in summary and has no keys")
        summary = ServiceInstance.api_get_keys(test_space.guid)
        self.assertIn(instance, summary)
        self.assertEqual(summary[instance], [])  # there are no keys for this instance
        self.step("Create a key for the instance and check it's correct")
        instance_key = ServiceInstanceKey.cf_api_create(instance.guid)
        summary = ServiceInstance.api_get_keys(test_space.guid)
        self.assertEqual(summary[instance][0], instance_key)

    def test_get_service_instance_summary_from_empty_space(self):
        self.step("Create a service instance in one space")
        service_type = next(iter([s for s in self.marketplace_services
                                  if s.label not in self.SERVICES_TESTED_SEPARATELY]))
        ServiceInstance.api_create(org_guid=self.test_org.guid, space_guid=self.test_org.spaces[0].guid,
                                   service_label=service_type.label,
                                   service_plan_guid=service_type.service_plan_guids[0])
        test_space = self.test_org.spaces[1]
        self.step("Get service instance summary in another space")
        summary = ServiceInstance.api_get_keys(test_space.guid)
        self.step("Check that service instance summary is empty in the second space")
        self.assertEqual(summary, {})

    def test_create_service_instance_keys(self):
        working_services = [s for s in self.marketplace_services if s.label not in self.SERVICES_TESTED_SEPARATELY]
        test_space = self.test_org.spaces[2]
        for service_type in working_services:
            for plan in service_type.service_plans:
                with self.subTest(service=service_type.label, plan=plan["name"]):
                    self._create_instance_and_key(service_type.label, plan["guid"], self.test_org, test_space)

    def test_create_yarn_service_instance_keys(self):
        """DPNG-3474 Command cf create-service-key does not work for yarn broker"""
        label = 'yarn'
        yarn = next(iter(s for s in self.marketplace_services if s.label == label))
        test_space = self.test_org.spaces[2]
        for plan in yarn.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_instance_and_key(label, plan["guid"], self.test_org, test_space)

    def test_create_hdfs_service_instance_keys(self):
        """TASK DPNG-3273 Enable HDFS broker to use Service Keys"""
        label = "hdfs"
        hdfs = next(iter(s for s in self.marketplace_services if s.label == label))
        test_space = self.test_org.spaces[2]
        for plan in hdfs.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_instance_and_key(label, plan["guid"], self.test_org, test_space)

    def test_create_hbase_service_instance_keys(self):
        """TASK DPNG-2798 Enable HBase broker to use Service Keys"""
        label = "hbase"
        hbase = next(iter(s for s in self.marketplace_services if s.label == label))
        test_space = self.test_org.spaces[2]
        for plan in hbase.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_instance_and_key(label, plan["guid"], self.test_org, test_space)

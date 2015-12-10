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
import unittest

from datetime import datetime

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import Organization, ServiceType, ServiceInstance, ServiceInstanceKey


class ServiceInstanceKeys(ApiTestCase):
    FAILING_SERVICES = ['yarn', 'hdfs', 'hbase', 'atk']

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test spaces")
        cls.test_org = Organization.api_create(space_names=("test-space", "test_space_a", "test_space_b"))
        cls.step("Get list of available services from Marketplace")
        cls.marketplace_services = ServiceType.api_get_list_from_marketplace(cls.test_org.spaces[0].guid)

    def _assert_key_creation(self, service_label, plan_guid, test_org, test_space):
        self.step("Create test service instance")
        service_instance_name = service_label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        instance = ServiceInstance.api_create(name=service_instance_name, service_plan_guid=plan_guid,
                                              space_guid=test_space.guid, org_guid=test_org.guid)
        self.step("Check if created service instance exist in summary")
        summary = ServiceInstance.api_get_summary(test_space.guid)
        self.assertInList(instance.guid, list(summary.keys()),
                          "Instance {} not found in summary".format(instance))
        self.step("Create key for created service instance and check its correctness")
        instance_key = ServiceInstanceKey.cf_api_create(instance.guid)
        summary = ServiceInstance.api_get_summary(test_space.guid)
        summary_keys = summary.get(instance_key.service_instance_guid, [])
        self.assertInList(instance_key, summary_keys, "Key {} not found in summary".format(instance_key))

    def test_get_service_instance_summary_from_empty_space(self):
        self.step("Create test instance in first space")
        service_type = next(iter(s for s in self.marketplace_services if s.label not in self.FAILING_SERVICES[0]))
        service_instance_name = service_type.label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        ServiceInstance.api_create(name=service_instance_name, service_plan_guid=service_type.service_plans[0]["guid"],
                                   space_guid=self.test_org.spaces[0].guid, org_guid=self.test_org.guid)
        test_space = self.test_org.spaces[1]
        self.step("Get service instances summary from different space")
        test_summary_list = ServiceInstance.api_get_summary(test_space.guid)
        self.step("Check if service instance summary is empty in second space")
        self.assertEqual(test_summary_list, {}, "Not empty summary was returned for newly created org")

    def test_working_creation_service_instance_keys(self):
        working_services = [s for s in self.marketplace_services if s.label not in self.FAILING_SERVICES]
        test_space = self.test_org.spaces[2]
        for service_type in working_services:
            for plan in service_type.service_plans:
                with self.subTest(service=service_type.label, plan=plan["name"]):
                    self._assert_key_creation(service_type.label, plan["guid"], self.test_org, test_space)

    @unittest.expectedFailure
    def test_create_yarn_service_instance_keys(self):
        """DPNG-3474 Command cf create-service-key does not work for yarn broker"""
        label = 'yarn'
        yarn = next(iter(s for s in self.marketplace_services if s.label == label))
        test_space = self.test_org.spaces[2]
        for plan in yarn.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._assert_key_creation(label, plan["guid"], self.test_org, test_space)

    @unittest.expectedFailure
    def test_create_hdfs_service_instance_keys(self):
        """DPNG-3273 Enable HDFS broker to use Service Keys"""
        label = "hdfs"
        hdfs = next(iter(s for s in self.marketplace_services if s.label == label))
        test_space = self.test_org.spaces[2]
        for plan in hdfs.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._assert_key_creation(label, plan["guid"], self.test_org, test_space)

    @unittest.expectedFailure
    def test_create_hbase_service_instance_keys(self):
        """DPNG-2798 Enable HBase broker to use Service Keys"""
        label = "hbase"
        hbase = next(iter(s for s in self.marketplace_services if s.label == label))
        test_space = self.test_org.spaces[2]
        for plan in hbase.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._assert_key_creation(label, plan["guid"], self.test_org, test_space)

    @unittest.skip
    @unittest.expectedFailure
    def test_create_atk_service_instance_keys(self):
        """DPNG-3788 502 bad gateway while creating ATK instance"""
        label = "atk"
        atk = next(iter(s for s in self.marketplace_services if s.label == label))
        test_space = self.test_org.spaces[2]
        for plan in atk.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._assert_key_creation(label, plan["guid"], self.test_org, test_space)

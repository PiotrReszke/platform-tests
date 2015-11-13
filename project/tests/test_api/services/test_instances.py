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
    FAILING_SERVICES = ['yarn', 'atk', 'hdfs', 'zookeeper', 'postgresql93', 'mysql56', 'redis28', 'mongodb26',
                        'couchdb16', 'neo4j21', 'arangodb22', 'rabbitmq33', 'memcached14', 'elasticsearch13',
                        'logstash14', 'nats', 'etcd', 'rethinkdb', 'influxdb088', 'mosquitto14', 'ipython', 'rstudio',
                        'hbase', 'gateway']
    WORKING_SERVICES = ['zookeeper-wssb',  'kafka', 'smtp', 'cdh']

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test spaces")
        cls.test_org = Organization.api_create(space_names=("test-space", "test_space_a", "test_space_b"))
        cls.step("Get list of available services from Marketplace")
        cls.marketplace_services = ServiceType.api_get_list_from_marketplace(cls.test_org.spaces[0].guid)

    @classmethod
    def _create_instance(cls, service_type, plan, test_org, test_space):
        service_instance_name = service_type.label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return ServiceInstance.api_create(name=service_instance_name, service_plan_guid=plan['guid'],
                                          space_guid=test_space.guid, org_guid=test_org.guid)

    def _test_service_and_keys_creation(self, service_list, test_org, test_space):
        for service_type in service_list:
            for plan in service_type.service_plans:
                with self.subTest(service=service_type, plan=plan):
                    self.step("Create test service instance")
                    instance = self._create_instance(service_type, plan, test_org, test_space)
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
        service_type = next(iter([s for s in self.marketplace_services if s.label == self.WORKING_SERVICES[0]]))
        self._create_instance(service_type, service_type.service_plans[0], self.test_org, self.test_org.spaces[0])
        test_space = self.test_org.spaces[1]
        self.step("Get service instances summary from different space")
        test_summary_list = ServiceInstance.api_get_summary(test_space.guid)
        self.step("Check if service instance summary is empty in second space")
        self.assertEqual(test_summary_list, {}, "Not empty summary was returned for newly created org")

    def test_working_creation_service_instance_keys(self):
        working_services = [s for s in self.marketplace_services if s.label in self.WORKING_SERVICES]
        test_space = self.test_org.spaces[2]
        self._test_service_and_keys_creation(working_services, self.test_org, test_space)

    @unittest.expectedFailure
    def test_failing_creation_service_instance_keys(self):
        """DPNG-3233 Creation of service keys for docker services does not work"""
        failing_services = [s for s in self.marketplace_services if s.label in self.FAILING_SERVICES]
        test_space = self.test_org.spaces[2]
        self._test_service_and_keys_creation(failing_services, self.test_org, test_space)

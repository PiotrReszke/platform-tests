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

from datetime import datetime
import unittest

from test_utils import ApiTestCase, get_logger
from objects import ServiceInstance, ServiceType, Organization


logger = get_logger("test marketplace")


class TestMarketplaceServices(ApiTestCase):

    @classmethod
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_organization = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_organization.spaces[0]
        cls.step("Get list of available services from Marketplace")
        cls.platform_marketplace_services = ServiceType.api_get_list_from_marketplace(cls.test_space.guid)

    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()

    def _test_service_instance_creation_and_deletion(self, service_type):
        for plan in service_type.service_plans:
            with self.subTest(service=service_type, plan=plan['name']):
                self.step("Create instance of {} ({} plan). Check it exists.".format(service_type.label, plan["name"]))
                service_instance_name = service_type.label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                instance = ServiceInstance.api_create(name=service_instance_name,
                                                      service_plan_guid=plan['guid'],
                                                      space_guid=service_type.space_guid,
                                                      org_guid=self.test_organization.guid)
                self.assertIsNotNone(instance, "{} instance was not created".format(service_type))
                self.step("Delete the instance and check it no longer exists")
                instance.api_delete()
                instances = ServiceInstance.api_get_list(space_guid=service_type.space_guid,
                                                         service_type_guid=service_type.guid)
                self.assertNotInList(instance, instances, "{} instance was not deleted".format(service_type))

    def test_check_marketplace_services_list_vs_cloudfoundry(self):
        self.step("Check that services in cf are the same as in Marketplace")
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace(self.test_space.guid)
        self.assertUnorderedListEqual(self.platform_marketplace_services, cf_marketplace)

    def test_create_gateway_instance(self):
        """DPNG-3177 Cannot create gateway instance - 502 Bad Gateway"""
        label = "gateway"
        self.step("Check that {} service is available in Marketplace".format(label))
        service_type = next((st for st in self.platform_marketplace_services if st.label == label), None)
        self.assertIsNotNone(service_type, "{} service is not available in Marketplace".format(label))
        self._test_service_instance_creation_and_deletion(service_type)

    def test_create_zookeeper_instance(self):
        """DPNG-2130 Cannot create zookeeper instance on Ireland - Bad Gateway"""
        label = "zookeeper"
        self.step("Check that {} service is available in Marketplace".format(label))
        service_type = next((st for st in self.platform_marketplace_services if st.label == label), None)
        self.assertIsNotNone(service_type, "{} service is not available in Marketplace".format(label))
        self._test_service_instance_creation_and_deletion(service_type)

    def test_create_hbase_instance(self):
        """DPNG-2299 Error when creating hbase service instance in Marketplace"""
        label = "hbase"
        self.step("Check that {} service is available in Marketplace".format(label))
        service_type = next((st for st in self.platform_marketplace_services if st.label == label), None)
        self.assertIsNotNone(service_type, "{} service is not available in Marketplace".format(label))
        self._test_service_instance_creation_and_deletion(service_type)

    def test_create_hdfs_instance(self):
        """DPNG-2580 Creating instance of hdfs with plan encrypted fails with 502 Bad Gateway"""
        label = "hdfs"
        self.step("Check that {} service is available in Marketplace".format(label))
        service_type = next((st for st in self.platform_marketplace_services if st.label == label), None)
        self.assertIsNotNone(service_type, "{} service is not available in Marketplace".format(label))
        self._test_service_instance_creation_and_deletion(service_type)

    def test_create_memcached14_instance(self):
        """DPNG-2476 Cannot create memcached14 1Gb instance on Ireland - Bad Gateway"""
        label = "memcached14"
        self.step("Check that {} service is available in Marketplace".format(label))
        service_type = next((st for st in self.platform_marketplace_services if st.label == label), None)
        self.assertIsNotNone(service_type, "{} service is not available in Marketplace".format(label))
        self._test_service_instance_creation_and_deletion(service_type)

    def test_create_instance_of_other_services(self):
        # excluded services are tested elsewhere or are not to be tested
        excluded_services = ("atk", "gateway", "h2oUC", "h2oUC-docker", "hbase", "hdfs", "hello", "simple-hello-env",
                             "zookeeper", "pg-test-pz", "hdfs-oauth", "hdfs-alpha", "memcached14")
        tested_service_types = [st for st in self.platform_marketplace_services if st.label not in excluded_services]
        for service_type in tested_service_types:
            self._test_service_instance_creation_and_deletion(service_type)


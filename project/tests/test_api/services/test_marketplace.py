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

from test_utils import ApiTestCase, get_logger
from objects import ServiceInstance, ServiceType, Organization


logger = get_logger("test marketplace")


class TestMarketplaceServices(ApiTestCase):

    SERVICES_TESTED_SEPARATELY = ("atk", "gateway", "hdfs", "scoring-engine")

    @classmethod
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Get list of available services from Marketplace")
        cls.marketplace = ServiceType.api_get_list_from_marketplace(cls.test_space.guid)

    def _create_and_delete_service_instance(self, org_guid, space_guid, service_label, plan_guid):
        self.step("Create service instance")
        instance = ServiceInstance.api_create(
            org_guid=org_guid,
            space_guid=space_guid,
            service_label=service_label,
            service_plan_guid=plan_guid
        )
        self.step("Check that the instance was created")
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        self.assertInList(instance, instances)
        self.step("Delete the instance")
        instance.api_delete()
        self.step("Check that the instance was deleted")
        instances = ServiceInstance.api_get_list(space_guid=space_guid)
        self.assertNotInList(instance, instances)

    def test_check_marketplace_services_list_vs_cloudfoundry(self):
        self.step("Check that services in cf are the same as in Marketplace")
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace(self.test_space.guid)
        self.assertUnorderedListEqual(self.marketplace, cf_marketplace)

    def test_create_and_delete_service_instance(self):
        tested_service_types = [st for st in self.marketplace if st.label not in self.SERVICES_TESTED_SEPARATELY]
        for service_type in tested_service_types:
            for plan in service_type.service_plans:
                with self.subTest(service=service_type.label, plan=plan["name"]):
                    self._create_and_delete_service_instance(self.test_org.guid, self.test_space.guid,
                                                             service_type.label, plan["guid"])

    @unittest.expectedFailure
    def test_create_gateway_instance(self):
        """DPNG-4338 Adjust service creation test to handle 200 and 504 codes"""
        label = "gateway"
        self.step("Check that {} service is available in Marketplace".format(label))
        service_type = next((st for st in self.marketplace if st.label == label), None)
        self.assertIsNotNone(service_type, "{} service is not available in Marketplace".format(label))
        for plan in service_type.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_and_delete_service_instance(self.test_org.guid, self.test_space.guid, label, plan["guid"])

    def test_create_hdfs_instance(self):
        """DPNG-2580 Creating instance of hdfs with plan encrypted fails with 502 Bad Gateway"""
        label = "hdfs"
        self.step("Check that {} service is available in Marketplace".format(label))
        service_type = next((st for st in self.marketplace if st.label == label), None)
        self.assertIsNotNone(service_type, "{} service is not available in Marketplace".format(label))
        for plan in service_type.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_and_delete_service_instance(self.test_org.guid, self.test_space.guid, label, plan["guid"])

    @unittest.expectedFailure
    def test_create_atk_instance(self):
        """DPNG-3788 502 bad gateway while creating ATK instance"""
        label = "atk"
        self.step("Check that {} service is available in Marketplace".format(label))
        service_type = next((st for st in self.marketplace if st.label == label), None)
        self.assertIsNotNone(service_type, "{} service is not available in Marketplace".format(label))
        for plan in service_type.service_plans:
            with self.subTest(service=label, plan=plan["name"]):
                self._create_and_delete_service_instance(self.test_org.guid, self.test_space.guid, label, plan["guid"])


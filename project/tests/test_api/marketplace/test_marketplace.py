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

    def setUp(self):
        self.test_organization = Organization.api_create(space_names=("test-space",))
        self.test_space = self.test_organization.spaces[0]
        self.platform_marketplace_services = ServiceType.api_get_list_from_marketplace(self.test_space.guid)

    def tearDown(self):
        Organization.cf_api_tear_down_test_orgs()

    def _test_service_instance_creation_and_deletion(self, service_type):
        service_instance_name = service_type.label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        instance = ServiceInstance.api_create(name=service_instance_name,
                                              service_plan_guid=service_type.service_plan_guids[0],
                                              space_guid=service_type.space_guid,
                                              org_guid=self.test_organization.guid)
        self.assertIsNotNone(instance, "{} instance was not created".format(service_type))
        instance.api_delete()
        instances = ServiceInstance.api_get_list(space_guid=service_type.space_guid,
                                                 service_type_guid=service_type.guid)
        self.assertNotInList(instance, instances, "{} instance was not deleted".format(service_type))

    def test_marketplace_services(self):
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace(self.test_space.guid)
        self.assertUnorderedListEqual(self.platform_marketplace_services, cf_marketplace)

    def test_create_gateway_instance(self):
        service_type = next(st for st in self.platform_marketplace_services if st.label == "gateway")
        self._test_service_instance_creation_and_deletion(service_type)

    @unittest.expectedFailure
    def test_create_rstudio_proxy_instance(self):
        """DPNG-2297 Cannot create instance of rstudio-proxy from Marketplace"""
        service_type = next(st for st in self.platform_marketplace_services if st.label == "rstudio-proxy")
        self._test_service_instance_creation_and_deletion(service_type)

    @unittest.expectedFailure
    def test_create_zookeeper_instance(self):
        """DPNG-2130 Cannot create zookeeper instance on Ireland - Bad Gateway"""
        service_type = next(st for st in self.platform_marketplace_services if st.label == "zookeeper")
        self._test_service_instance_creation_and_deletion(service_type)

    @unittest.expectedFailure
    def test_create_hbase_instance(self):
        """DPNG-2299 Error when creating hbase service instance in Marketplace"""
        service_type = next(st for st in self.platform_marketplace_services if st.label == "hbase")
        self._test_service_instance_creation_and_deletion(service_type)

    def test_create_hdfs_instance(self):
        service_type = next(st for st in self.platform_marketplace_services if st.label == "hdfs")
        self._test_service_instance_creation_and_deletion(service_type)

    def test_create_instance_of_other_services(self):
        # excluded services are tested elsewhere or are not to be tested
        excluded_services = ("atk", "gateway", "h2oUC", "h2oUC-docker", "hbase", "hdfs", "ipython", "ipython-proxy",
                             "piotr-hdfs", "rstudio-proxy", "zookeeper")
        tested_service_types = [st for st in self.platform_marketplace_services if st.label not in excluded_services]
        for service_type in tested_service_types:
            with self.subTest(service=service_type):
                self._test_service_instance_creation_and_deletion(service_type)


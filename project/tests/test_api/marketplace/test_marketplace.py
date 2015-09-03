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

from objects import ServiceType, Organization, ServiceInstance
from test_utils import ApiTestCase, get_logger


logger = get_logger("test marketplace")


class TestMarketplaceServices(ApiTestCase):

    def setUp(self):
        self.test_organization = Organization.api_create(space_names=("test-space",))
        self.test_space = self.test_organization.spaces[0]

    def tearDown(self):
        Organization.cf_api_tear_down_test_orgs()

    def test_marketplace_services(self):
        api_marketplace = ServiceType.api_get_list_from_marketplace(self.test_space.guid)
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace(self.test_space.guid)
        self.assertCountEqual(api_marketplace, cf_marketplace)

    def test_create_instance_of_every_service(self):
        excluded_services = ("atk", "ipython-proxy", "ipython")  # services which are tested elsewhere
        marketplace_services = ServiceType.api_get_list_from_marketplace(self.test_space.guid)
        for service_type in marketplace_services:
            if service_type.label not in excluded_services:
                with self.subTest(service=service_type):
                    service_instance_name = service_type.label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    instance = ServiceInstance.api_create(
                        name=service_instance_name,
                        service_plan_guid=service_type.service_plan_guids[0],
                        space_guid=service_type.space_guid,
                        org_guid=self.test_organization.guid
                    )
                    self.assertIsNotNone(instance,
                                         "Instance of {} was not found on service instance list".format(service_type))

                    instance.api_delete()
                    instances = ServiceInstance.api_get_list(space_guid=service_type.space_guid,
                                                             service_type_guid=service_type.guid)
                    self.assertNotInList(instance, instances)

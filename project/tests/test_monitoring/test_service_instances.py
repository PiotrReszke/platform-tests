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

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import Organization, ServiceInstance, ServiceType


class ServiceInstancesMonitoring(ApiTestCase):

    TESTED_APP_NAMES = {"rstudio"}

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_organization = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_organization.spaces[0]
        cls.step("Get list of available services from Marketplace")
        cls.marketplace_services = ServiceType.api_get_list_from_marketplace(cls.test_space.guid)

    def test_service_instances(self):
        tested_service_types = [st for st in self.marketplace_services if st.label in self.TESTED_APP_NAMES]
        for service_type in tested_service_types:
            for plan in service_type.service_plans:
                with self.subTest(service=service_type.label, plan=plan["name"]):
                    self.step("Create instance of {} ({} plan). Check it exists.".format(service_type.label,
                                                                                         plan["name"]))
                    service_instance_name = service_type.label + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    instance = ServiceInstance.api_create(
                        org_guid=self.test_organization.guid,
                        space_guid=service_type.space_guid,
                        service_label=service_type.label,
                        name=service_instance_name,
                        service_plan_guid=plan['guid']
                    )
                    self.assertIsNotNone(instance, "{} instance was not created".format(service_type))
                    self.step("Delete the instance and check it no longer exists")
                    instance.api_delete()
                    instances = ServiceInstance.api_get_list(space_guid=service_type.space_guid,
                                                             service_type_guid=service_type.guid)
                    self.assertNotIn(instance, instances, "{} instance was not deleted".format(service_type))

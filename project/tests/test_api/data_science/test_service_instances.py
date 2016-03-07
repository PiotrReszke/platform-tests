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

from test_utils import ApiTestCase, priority
from objects import ServiceInstance, ServiceType, Organization, Application
from objects.service_instance_validator import ServiceInstanceValidator
from constants.services import ServiceLabels


class ServiceInstances(ApiTestCase):
    @classmethod
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Get marketplace services")
        cls.marketplace = ServiceType.api_get_list_from_marketplace(cls.test_space.guid)

    def _create_instance(self, org_guid, space_guid, service_label, plan_guid):
        self.step("Create service instance")
        return ServiceInstance.api_create(
            org_guid=org_guid,
            space_guid=space_guid,
            service_label=service_label,
            service_plan_guid=plan_guid
        )

    def _delete_instance(self, instance):
        self.step("Delete service instance")
        instance.api_delete()

    @priority.high
    def test_create_and_delete_service_instances(self):
        services = [ServiceLabels.IPYTHON, ServiceLabels.RSTUDIO]
        for service_type in [s for s in self.marketplace if s.label in services]:
            plan = next(iter(service_type.service_plans))
            with self.subTest(service=service_type.label):
                instance = self._create_instance(
                    self.test_org.guid, self.test_space.guid, service_type.label, plan["guid"])
                validator = ServiceInstanceValidator(self, instance)
                validator.validate(validate_application=False)
                self._delete_instance(instance)
                validator.validate_removed()

    @priority.high
    def test_create_and_delete_atk_instance(self):
        self.step("Get reference bound services")
        ref_space_guid = Organization.get_ref_org_and_space()[1].guid
        ref_atk_app = next((a for a in Application.api_get_list(ref_space_guid) if a.name == "atk"), None)
        self.assertIsNotNone(ref_atk_app, "ATK app not found in seedspace")
        expected_bindings = [s[0]["label"] for s in ref_atk_app.cf_api_env()["VCAP_SERVICES"].values()]
        self.step("Get tested service type")
        service_type = next(s for s in self.marketplace if s.label == ServiceLabels.ATK)
        plan = next(iter(service_type.service_plans))
        instance = self._create_instance(self.test_org.guid, self.test_space.guid, service_type.label, plan["guid"])
        validator = ServiceInstanceValidator(self, instance)
        validator.validate(expected_bindings=expected_bindings)
        self._delete_instance(instance)
        validator.validate_removed()

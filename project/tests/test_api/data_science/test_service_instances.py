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

from retry import retry

from test_utils import ApiTestCase
from objects import ServiceInstance, ServiceType, Organization, Application, AtkInstance


class TestServiceInstancesDeletion(ApiTestCase):
    @classmethod
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Get marketplace services")
        cls.marketplace = ServiceType.api_get_list_from_marketplace(cls.test_space.guid)

    def _create_service_instance(self, org_guid, space_guid, service_label, plan_guid):
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
        return instance

    def _delete_service_instance(self, instance):
        instance.api_delete()
        service_instances = ServiceInstance.api_get_list(self.test_space.guid)
        self.assertNotInList(instance, service_instances)

    @retry(AssertionError, tries=10, delay=5)
    def _check_data_science_service_instance(self, instance_name, label):
        ds_instances = ServiceInstance.api_get_data_science_service_instances(self.test_space.guid, self.test_org.guid,
                                                                              label)
        self.assertInList(instance_name, ds_instances.keys())

    def test_create_and_delete_service_instances(self):
        services = ["ipython", "rstudio"]
        for service_type in [s for s in self.marketplace if s.label in services]:
            plan = next(iter(service_type.service_plans))
            with self.subTest(service=service_type.label):
                instance = self._create_service_instance(self.test_org.guid, self.test_space.guid, service_type.label,
                                                         plan["guid"])
                self.step("Check data science {} instance list".format(service_type.label))
                self._check_data_science_service_instance(instance.name, service_type.label)
                self.step("Delete service instance and check it does not show on the list")
                self._delete_service_instance(instance)

    def test_create_and_delete_atk_instance(self):
        service_name = "atk"
        self.step("Get reference bound services")
        ref_space_guid = Organization.get_ref_org_and_space()[1].guid
        ref_atk_app = next((a for a in Application.api_get_list(ref_space_guid) if a.name == "atk"), None)
        self.assertIsNotNone(ref_atk_app, "ATK app not found in seedspace")
        ref_bound_services = [s[0]["label"] for s in ref_atk_app.cf_api_env()["VCAP_SERVICES"].values()]
        self.step("Get tested service type")
        service_type = next(s for s in self.marketplace if s.label == service_name)
        plan = next(iter(service_type.service_plans))
        instance = self._create_service_instance(self.test_org.guid, self.test_space.guid, service_type.label,
                                                 plan["guid"])
        self.step("Check that created atk instance exists in data science atk list")
        data_science_atk_list = AtkInstance.api_get_list_from_data_science_atk(self.test_org.guid)
        self.assertInList(instance.name, [i.name for i in data_science_atk_list],
                          "Atk not found in data science atk list")
        self.step("Check that atk exists in application list")
        atk_app_name = instance.name + "-{}".format(instance.guid[:8])
        atk_app = next((a for a in Application.api_get_list(self.test_space.guid) if a.name == atk_app_name), None)
        self.assertIsNotNone(atk_app, "ATK app not found")
        bound_services = {s[0]["label"]: s[0]["name"] for s in atk_app.cf_api_env()["VCAP_SERVICES"].values()}
        self.step("Check bound service types with reference")
        self.assertUnorderedListEqual(ref_bound_services, bound_services.keys(),
                                      "Bound services are are not equal with expected")
        self.step("Check that all bound service instances exist")
        service_instances = [s.name for s in ServiceInstance.api_get_list(self.test_space.guid)]
        for s_name in bound_services.values():
            self.assertInList(s_name, service_instances)
        self.step("Delete service instance and check it does not show on the service list")
        self._delete_service_instance(instance)
        self.step("Check that atk instance was deleted from data science atk list")
        data_science_atk_list = AtkInstance.api_get_list_from_data_science_atk(self.test_org.guid)
        self.assertNotInList(instance.name, [i.name for i in data_science_atk_list],
                             "Atk found in data science atk list")
        self.step("Check that atk was deleted from application list")
        atk_app = next((a for a in Application.api_get_list(self.test_space.guid) if a.name == atk_app_name), None)
        self.assertIsNone(atk_app, "ATK app was found")
        self.step("Check that all bound service instances were deleted")
        service_instances = [s.name for s in ServiceInstance.api_get_list(self.test_space.guid)]
        for s_name in bound_services.values():
            self.assertNotInList(s_name, service_instances)


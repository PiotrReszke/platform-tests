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

import functools
import datetime

from test_utils import platform_api_calls as api, cloud_foundry as cf
from objects import ServiceInstanceKey


__all__ = ["ServiceInstance", "AtkInstance"]


@functools.total_ordering
class ServiceInstance(object):

    COMPARABLE_ATTRIBUTES = ["guid", "name", "space_guid"]

    def __init__(self, guid, name, space_guid=None, service_type_guid=None, type=None, url=None, org_guid=None,
                 service_plan_guid=None, credentials=None, bindings=None, login=None, password=None):
        self.guid, self.name, self.type, self.url = guid, name, type, url
        self.space_guid, self.org_guid = space_guid, org_guid
        self.service_type_guid, self.service_plan_guid = service_type_guid, service_plan_guid
        self.credentials, self.bindings = credentials, bindings
        self.login, self.password = login, password

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.guid < other.guid

    @classmethod
    def _from_cf_api_response(cls, org_guid, response):
        metadata = response["metadata"]
        entity = response["entity"]
        return cls(guid=metadata["guid"], name=entity["name"], type=entity["type"], url=metadata["url"],
                   org_guid=org_guid, space_guid=entity["space_guid"], service_plan_guid=entity["service_plan_guid"],
                   credentials=entity["credentials"])

    @classmethod
    def cf_api_get_list_for_org(cls, org_guid):
        service_instance_data = cf.cf_api_get_service_instances(org_guid)
        service_instances = []
        for data in service_instance_data:
            service_instances.append(cls._from_cf_api_response(org_guid, data))
        return service_instances

    @classmethod
    def from_cf_api_space_summary_response(cls, response, space_guid):
        instances = []
        for instance_data in response["services"]:
            service_type_guid = service_type = service_plan_guid = None
            instance_data_service_plan = instance_data.get("service_plan")
            if instance_data_service_plan:
                service_plan_guid = instance_data_service_plan.get("guid")
                service_plan = instance_data_service_plan.get("service")
                if service_plan:
                    service_type_guid = service_plan.get("guid")
                    service_type = service_plan.get("label")
            url = instance_data.get("dashboard_url")
            if url:
                url = url.replace("/dashboard", "")
            service_instance = cls(guid=instance_data["guid"], name=instance_data["name"], space_guid=space_guid,
                                   service_type_guid=service_type_guid, type=service_type, url=url,
                                   service_plan_guid=service_plan_guid)
            instances.append(service_instance)
        return instances

    @classmethod
    def cf_api_get_list(cls, space_guid):
        """Get list of service instances from Cloud Foundry API"""
        response = cf.cf_api_space_summary(space_guid)
        return cls.from_cf_api_space_summary_response(response, space_guid)

    @classmethod
    def api_get_list(cls, space_guid=None, org_guid=None, service_label=None, service_type_guid=None, client=None):
        instances = []
        response = api.api_get_service_instances(space_guid=space_guid, org_guid=org_guid, service_label=service_label,
                                                 service_guid=service_type_guid, client=client)
        for data in response:
            bindings = []
            for binding_data in data["bound_apps"]:
                bindings.append({
                    "app_guid": binding_data["guid"],
                    "service_instance_guid": data["guid"]
                })
            instance = cls(guid=data["guid"], name=data["name"], space_guid=space_guid,
                           service_type_guid=service_type_guid, bindings=bindings)
            instances.append(instance)
        return instances

    @classmethod
    def api_get_list_from_tools(cls, org_guid, space_guid, service_label, client=None):
        response = api.api_tools_service_instances(org_guid, service_label, space_guid, client)
        instances = []
        for name, data in response.items():
            instances.append(cls(guid=data["guid"], name=name, space_guid=space_guid, url=data["hostname"],
                             org_guid=org_guid, login=data["login"], password=data["password"]))
        return instances

    @classmethod
    def api_create(cls, name, service_plan_guid, org_guid, space_guid, client=None):
        response = api.api_create_service_instance(name, service_plan_guid, org_guid, space_guid, client=client)
        entity = response["entity"]
        return cls(guid=response["metadata"]["guid"], name=entity["name"], space_guid=space_guid, type=entity["type"],
                   service_plan_guid=service_plan_guid)

    @classmethod
    def cf_api_create(cls, space_guid, service_plan_guid, name_prefix):
        name = "{}_{}".format(name_prefix, datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        response = cf.cf_api_create_service_instance(name, space_guid, service_plan_guid)
        return cls(guid=response["metadata"]["guid"], name=name, space_guid=space_guid,
                   service_plan_guid=service_plan_guid)

    def api_delete(self, client=None):
        api.api_delete_service_instance(self.guid, client=client)

    @classmethod
    def api_get_summary(cls, space_guid, service_keys=True, client=None):
        summary_list = {}
        response = api.api_get_service_instances_summary(space_guid, service_keys, client)
        for summary in response:
            for instance in summary.get("instances", []):
                summary_list[instance['guid']] = [ServiceInstanceKey(guid=sk["guid"], name=sk["name"],
                                                                     credentials=sk["credentials"],
                                                                     service_instance_guid=sk["service_instance_guid"])
                                                  for sk in instance["service_keys"]]
        return summary_list


class AtkInstance(ServiceInstance):

    started_status = "STARTED"

    def __init__(self, guid, name, space_guid=None, service_type_guid=None, type=None, url=None, org_guid=None,
                 service_plan_guid=None, credentials=None, bindings=None, scoring_engine=None, state=None):
        super().__init__(guid=guid, name=name, space_guid=space_guid, service_type_guid=service_type_guid, type=type,
                         url=url, org_guid=org_guid, service_plan_guid=service_plan_guid, credentials=credentials,
                         bindings=bindings)
        self.state = state.upper() if state is not None else state
        self.scoring_engine = scoring_engine

    @classmethod
    def api_get_list(cls, org_guid, service_type_guid=None, client=None):
        response = api.api_get_atk_instances(org_guid, client=client)
        instances = []
        for data in response["instances"]:
            instance = cls(guid=data["guid"], name=data["name"], state=data["state"], url=data["url"],
                           scoring_engine=data["scoring_engine"], service_type_guid=data["service_guid"],
                           org_guid=org_guid, service_plan_guid=response["service_plan_guid"])
            instances.append(instance)
        return instances

    @classmethod
    def cf_create(cls, space_guid, service_type_guid=None, name=None, plan="simple"):
        """Do not use this if bug DPNG-1735 is fixed. Use API instead and remove this method."""
        name = name or "atk-test-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        cf.cf_create_service("atk", plan, name)
        service_instances = super().api_get_list(space_guid, service_type_guid)  # use cls.api_get_list() when DPNG-1735 is fixed
        return next((si for si in service_instances if si.name == name), None)

    def api_create_scoring_engine(self, instance_name, space_guid, client=None):
        api.api_create_scoring_engine(self.name, instance_name, space_guid, self.service_plan_guid, client=client)

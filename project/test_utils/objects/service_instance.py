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

import test_utils.cli.cloud_foundry as cf
import test_utils.api_calls.service_catalog_api_calls as api
import test_utils.api_calls.app_launcher_helper_api_calls as app_launcher_helper_api
from test_utils import get_admin_client


__all__ = ["ServiceInstance", "AtkInstance"]


@functools.total_ordering
class ServiceInstance(object):

    COMPARABLE_ATTRIBUTES = ["guid", "name", "space_guid"]

    def __init__(self, guid, name, space_guid=None, service_type_guid=None, type=None, url=None, org_guid=None,
                 service_plan_guid=None, credentials=None, bindings=None):
        self.guid = guid
        self.name = name
        self.space_guid = space_guid
        self.service_type_guid = service_type_guid
        self.type = type
        self.url = url
        self.org_guid = org_guid
        self.service_plan_guid = service_plan_guid
        self.credentials = credentials
        self.bindings = bindings

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
    def api_get_list(cls, space_guid, client=None):
        client = client or get_admin_client()
        instances = []
        response = api.api_get_service_instances(client, space_guid)
        for data in response:
            bindings = []
            for binding_data in data["bound_apps"]:
                bindings.append({
                    "app_guid": binding_data["guid"],
                    "service_instance_guid": data["guid"]
                })
            instance = cls(guid=data["guid"], name=data["name"], space_guid=space_guid, bindings=bindings)
            instances.append(instance)
        return instances

    @classmethod
    def api_create(cls, name, service_plan_guid, service_type_guid, space_guid, client=None):
        client = client or get_admin_client()
        api.api_create_service_instance(client, name, space_guid, service_plan_guid)
        # the response does not return service guid, it has to be retrieved from get
        instances = cls.api_get_list(space_guid, service_type_guid, client)
        return [i for i in instances if i["name"] == name][0]

    def api_delete(self, client=None):
        client = client or get_admin_client()
        api.api_delete_service_instance(client, self.guid)


class AtkInstance(ServiceInstance):

    def __init__(self, guid, name, state, scoring_engine, service_guid, url, org_guid, service_plan_guid):
        super().__init__(guid=guid, name=name, service_type_guid=service_guid, url=url, org_guid=org_guid,
                         service_plan_guid=service_plan_guid)
        self.state = state.upper()
        self.scoring_engine = scoring_engine

    @classmethod
    def get_list(cls, org_guid, client=None):
        client = client or get_admin_client()
        response = app_launcher_helper_api.api_get_atk_instances(client, org_guid)
        instances = []
        for data in response["instances"]:
            instance = cls(guid=data["guid"], name=data["name"], state=data["state"], url=data["url"],
                           scoring_engine=data["scoring_engine"], service_guid=data["service_guid"],
                           org_guid=org_guid, service_plan_guid=response["service_plan_guid"])
            instances.append(instance)
        return instances

    def api_create_scoring_engine(self, instance_name, space_guid, client=None):
        client = client or get_admin_client()
        api.api_create_scoring_engine(client, self.name, instance_name, space_guid, self.service_plan_guid)

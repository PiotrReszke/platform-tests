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
import random
import time

import test_utils.cli.cloud_foundry as cf_cli
import test_utils.api_calls.app_launcher_helper_api_calls as api
import test_utils.api_calls.service_catalog_api_calls as service_api
from test_utils.objects.user import get_admin_client

class CfBroker(object):

    def __init__(self, name):
        self.name = name
        plans = []
        output = cf_cli.cf_marketplace(service_name=self.name)
        # get plan from output, raise exception if not found
        plan_list = output.split("\n")[4].split(" ")
        for plan in plan_list:
            if plan != '':
                plans.append(plan)
        if not plans:
            raise Exception("No plans found. CfBroker object invalid")
        self.plan = plans[0]# get first plan from the list

    def is_available_in_cf(self):
        output = cf_cli.cf_marketplace(service_name=self.name)
        if "FAILED" in output:
            return False
        return True

    def cf_get_list(self):
        brokers = []
        output = cf_cli.cf_marketplace()
        # parse output and create CfBorker instances
        # for x in cośtam:
        #     broker.append(cls())
        return brokers

    @classmethod
    def cf_service_target(self, organization, space):
        cf_cli.cf_target(organization=organization, space=space)

@functools.total_ordering
class CfService(object):

    def __init__(self, broker_name=None, plan=None, name=None, URL=None, generated_name=None, guid=None):
        self.broker_name = broker_name
        self.name = name
        self.plan = plan
        self.URL = URL
        self.generated_name = generated_name
        self.guid = guid

    def __repr__(self):
        # return "{0} (name={1}, broker_name={2}, plan={3})".format(self.__class__.__name__, self.name, self.broker_name, self.plan)
        return "{0} (name={1})".format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    @classmethod
    def cf_get_list(cls):
        service_list = []
        output = cf_cli.cf_services()
        # parse output
        service_string_list = output.split("\n")[4:-1]
        for service_string in service_string_list:
            service_list.append(cls(None,None,service_string.split(" ")[0]))# get service name
        return service_list # CfService instances

    def has_broker_in_cf(self):
        broker = CfBroker(self.broker_name)
        return broker.is_available_in_cf()

    @classmethod
    def cf_create_instance(cls, broker_name, instance_name=None, plan="simple"):
        random_no = str(random.randrange(1000000)).zfill(6)
        instance_name = instance_name or "{}{}".format(broker_name, random_no)
        try:
            cf_cli.cf_create_service(broker_name, plan, instance_name)
        except Exception:
            raise Exception("service ATK not created properly")
        return cls(broker_name=broker_name, plan=plan, name=instance_name)

    def add_URL_and_generated_name(self, orgs, client=None):
        client = client or get_admin_client()
        instances = api.api_get_atk_instances(client, orgs)
        instance_URL = None
        for i in range(len(instances['instances'])):
            if instances['instances'][i]['name'] == self.name:
                instance_URL = instances['instances'][i]['url']
        if instance_URL == None or len(instance_URL) == 0:
            raise Exception("instance not found")
        self.URL = instance_URL
        self.generated_name = self.URL.split(".", 1)[0]  #automatically generated name is part of instance URL

    def add_URL_and_generated_name_via_space(self, space, client=None):
        client = client or get_admin_client()
        instances = service_api.api_get_filtered_applications(client, space)
        self.URL = instances[0]["urls"][0]
        self.generated_name = instances[0]["name"]

    def delete_all_binds(self, services_bound):
        for service in services_bound:
            cf_cli.cf_unbind_service(self.generated_name, service.name)

    def cf_delete(self):
        cf_cli.cf_delete_with_routes(self.generated_name)

    def api_delete(self, client=None):
        client = client or get_admin_client()
        return service_api.api_delete_app(client, self.guid)



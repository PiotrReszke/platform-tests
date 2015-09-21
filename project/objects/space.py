#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from datetime import datetime
import functools

from . import Application, ServiceInstance
from test_utils import platform_api_calls as api, cloud_foundry as cf, UnexpectedResponseError, get_logger


__all__ = ["Space"]

logger = get_logger("space")


@functools.total_ordering
class Space(object):
    NAME_PREFIX = "test_space_"

    def __init__(self, name, guid=None, org_guid=None):
        self.name = name
        self.guid = guid
        self.org_guid = org_guid

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    # -------------------------------- platform api -------------------------------- #

    @classmethod
    def api_create(cls, org=None, name=None, client=None):
        if name is None:
            name = cls.NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        response = api.api_create_space(org.guid, name, client=client)
        space = cls(name=name, guid=response, org_guid=org.guid)
        org.spaces.append(space)
        return space

    @classmethod
    def api_get_list(cls, client=None):
        response = api.api_get_spaces(client)
        spaces = []
        for space_data in response:
            org_guid = space_data["entity"]["organization_guid"]
            name = space_data["entity"]["name"]
            guid = space_data["metadata"]["guid"]
            spaces.append(cls(name, guid, org_guid))
        return spaces

    def api_delete(self, org=None, client=None):
        api.api_delete_space(self.guid, client=client)
        if org:
            org.spaces.remove(self)

    # -------------------------------- cf api -------------------------------- #

    def delete_associations(self):
        """Delete applications, service instances, and routes"""
        apps = self.cf_api_get_space_summary()[0]
        for app in apps:
            app.api_delete(cascade=True)
        service_instances = self.cf_api_get_space_summary()[1]  # app deletion deletes bound service instances
        for service_instance in service_instances:
            try:
                service_instance.api_delete()  # delete using api due to cf timeouts with atk instances: DPNG-1737
            except UnexpectedResponseError as e:
                if e.status == 404:
                    logger.info(
                        "This is an expected error as service {} could be removed together with application".format(
                            service_instance.name))
                elif e.status == 500 and "Read timed out" in e.error_message:
                    logger.info(
                        "Server returned expected while deleting {}: Read timed out".format(service_instance.name))
                else:
                    raise
        self.cf_api_delete_routes()

    def cf_api_get_space_summary(self):
        """Return tuple with list of Application and ServiceInstance objects."""
        response = cf.cf_api_space_summary(self.guid)
        apps = Application.from_cf_api_space_summary_response(response, self.guid)
        service_instances = ServiceInstance.from_cf_api_space_summary_response(response, self.guid)
        return apps, service_instances

    @classmethod
    def cf_api_get_list(cls):
        response = cf.cf_api_get_spaces()
        spaces = []
        for space_data in response:
            org_guid = space_data["entity"]["organization_guid"]
            name = space_data["entity"]["name"]
            guid = space_data["metadata"]["guid"]
            spaces.append(cls(name, guid, org_guid))
        return spaces

    def cf_api_delete(self):
        cf.cf_api_delete_space(self.guid)

    def cf_api_delete_routes(self):
        route_info = cf.cf_api_get_space_routes(self.guid)
        route_guids = [route_data["metadata"]["guid"] for route_data in route_info["resources"]]
        for route_guid in route_guids:
            cf.cf_api_delete_route(route_guid)


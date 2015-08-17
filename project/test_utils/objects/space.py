from datetime import datetime
import functools

import test_utils.cli.cloud_foundry as cf
from test_utils.objects import User, Application, ServiceInstance
from test_utils import get_config_value, get_admin_client
import test_utils.api_calls.user_management_api_calls as api


__all__ = ["Space"]


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

    @classmethod
    def delete_spaces_in_org(self, client=None, org_guid=None):
        client = client or get_admin_client()
        spaces = Space.get_list(client, org_guid=org_guid)
        if spaces:
            for space in spaces:
                space.delete()    
                
    # @classmethod
    # def api_create(cls, org_guid=None, name=None, client=None):
    #     client = client or get_admin_client()
    #     if name is None:
    #         name = cls.NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
    #     api.api_create_space(client, org_guid, name)
    #     spaces = Space.api_get_list(client)
    #     for space in spaces:
    #         if org_guid == space.org_guid and name == space.name:
    #             return space

    @classmethod
    def api_create(cls, org=None, name=None, client=None):
        client = client or get_admin_client()
        if name is None:
            name = cls.NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        api.api_create_space(client, org.guid, name)
        spaces = Space.api_get_list(client)
        for space in spaces:
            if org.guid == space.org_guid and name == space.name:
                org.spaces.append(space)
                return space

    @classmethod
    def api_get_list(cls, client=None):
        client = client or get_admin_client()
        response = api.api_get_spaces(client)
        spaces = []
        for space_data in response:
            org_guid = space_data["entity"]["organization_guid"]
            name = space_data["entity"]["name"]
            guid = space_data["metadata"]["guid"]
            spaces.append(cls(name, guid, org_guid))
        return spaces

    def api_delete(self, org=None, client=None):
        client = client or get_admin_client()
        api.api_delete_space(client, self.guid)
        if org:
            org.spaces.remove(self)

    def delete_associations(self):
        """Delete applications, service instances, and routes"""
        apps = self.cf_api_get_space_summary()[0]
        for app in apps:
            app.api_delete(cascade=True)
        service_instances = self.cf_api_get_space_summary()[1]  # app deletion deletes bound service instances
        for service_instance in service_instances:
            service_instance.api_delete()  # delete using api due to cf timeouts with atk instances: DPNG-1737
        route_info = cf.cf_api_get_space_routes(self.guid)
        route_guids = [route_data["metadata"]["guid"] for route_data in route_info["resources"]]
        for route_guid in route_guids:
            cf.cf_api_delete_route(route_guid)

    def cf_api_get_space_summary(self):
        """Return tuple with list of Application and ServiceInstance objects."""
        response = cf.cf_api_space_summary(self.guid)
        apps = Application.from_cf_api_space_summary_response(response, self.guid)
        service_instances = ServiceInstance.from_cf_api_space_summary_response(response, self.guid)
        return apps, service_instances

    def add_admin(self, org_guid, roles=("developers",)):
        admin = User.get_admin_user(org_guid)
        admin.add_to_space(org_guid, self.guid, list(roles))


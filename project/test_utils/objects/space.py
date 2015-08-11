from datetime import datetime
import functools
import time

from test_utils import get_config_value, get_admin_client
import test_utils.cli.cloud_foundry as cf
from test_utils.objects import Application, ServiceInstance, User
from test_utils import get_config_value, get_admin_client
import test_utils.api_calls.user_management_api_calls as api
from test_utils.objects.user import User


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
    def get_seedspace(cls):
        return cls(name="seedspace", guid=get_config_value("seedspace_guid"))

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

    def cf_delete_everything(self, org_object):
        apps, service_instances = self.cf_api_get_space_summary()
        for app in apps:
            app.cf_delete()
        for service_instance in service_instances:
            try:
                service_instance.api_delete()  # deleting using api due to cf timeouts on deleting atk instances: DPNG-1737
            except:
                pass  #service instance should be deleted together with app but sometimes it takes longer than script is running and server returns 404
        # deleting routes
        routes = []
        routes_string = cf.cf_routes().split("\n")[3:]
        for route_data in routes_string:
            if route_data != "":
                routes.append(route_data)
        if routes[0] != "No routes found":
            for route in routes:
                cf.cf_delete_route(domain=get_config_value("api_endpoint"), route=route.split(" ", 1)[0])

    def cf_api_get_space_summary(self):
        """Return tuple with list of Application and ServiceInstance objects."""
        response = cf.cf_api_space_summary(self.guid)
        apps = Application.from_cf_api_space_summary_response(response, self.guid)
        service_instances = ServiceInstance.from_cf_api_space_summary_response(response, self.guid)
        return apps, service_instances

    def add_admin(self, org_guid, roles=("developers",)):
        admin = User.get_admin()
        admin.add_to_space(org_guid, self.guid, list(roles))

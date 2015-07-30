import functools
from datetime import datetime

from test_utils import get_config_value, get_admin_client
import test_utils.api_calls.user_management_api_calls as api


__all__ = ["Space"]


@functools.total_ordering
class Space(object):

    NAME_PREFIX = "test_space_"

    def __init__(self, name, guid):
        self.name = name
        self.guid = guid

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
    def create(cls, client=None, name=None, org_guid=None):
        client = client or get_admin_client()
        if name is None:
            name = cls.NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        api.api_create_space(client, name, org_guid)

        # space guid is not returned in the response, so it must be acquired from orgs list
        space_guid = None
        orgs = api.api_get_organizations(client)
        for org in orgs:
            if org["guid"] == org_guid:
                for space in org["spaces"]:
                    if space["name"] == name:
                        space_guid = space["guid"]

        new_space = cls(name=name, guid=space_guid)
        return new_space

    def delete(self, client=None):
        client = client or get_admin_client()
        api.api_delete_space(client, space=self.guid)

    @classmethod
    def get_list(cls, client=None, org_guid=None):
        client = client or get_admin_client()
        spaces = []
        if org_guid is None:
            orgs = api.api_get_organizations(client)
            for org in orgs:
                    for space in org["spaces"]:
                        spaces.append(cls(name=space["name"], guid=space["guid"]))
        else:
            orgs = api.api_get_organizations(client)
            for org in orgs:
                if org["guid"] == org_guid:
                    for space in org["spaces"]:
                        spaces.append(cls(name=space["name"], guid=space["guid"]))
        return spaces

    @classmethod
    def delete_spaces_in_org(self, client=None, org_guid=None):
        client = client or get_admin_client()
        spaces = Space.get_list(client, org_guid=org_guid)
        if spaces:
            for space in spaces:
                space.delete()
import functools
import time

import test_utils.user_management.api_calls as api


@functools.total_ordering
class User(object):

    def __init__(self, guid, username, roles=None, organization_guid=None, space_guid=None):
        self.guid = guid
        self.username = username
        self.roles = [] if roles is None else roles
        self.organization_guid = organization_guid
        self.space_guid = space_guid

    def __repr__(self):
        return "{0} (username={1}, guid={2})".format(self.__class__.__name__, self.username, self.guid)

    def __eq__(self, other):
        return (self.username == other.username and self.guid == other.guid and sorted(self.roles) == sorted(other.roles) and
                self.organization_guid == other.organization_guid and self.space_guid == other.space_guid)

    def __lt__(self, other):
        return self.guid < other.guid

    @staticmethod
    def get_default_username(prefix="test-user-"):
        return prefix + str(time.time()) + "@example.com"

    @classmethod
    def create_via_organization(cls, organization_guid, username=None, roles=None):
        username = cls.get_default_username() if username is None else username
        response = api.api_create_organization_user(organization_guid, username, roles)
        return cls(guid=response["guid"], username=username, roles=roles, organization_guid=organization_guid)

    @classmethod
    def create_via_space(cls, space_guid, organization_guid=None, username=None, roles=None):
        username = cls.get_default_username() if username is None else username
        response = api.api_create_space_user(space_guid, username, organization_guid, roles)
        return cls(guid=response["guid"], username=username, roles=roles, organization_guid=response["org_guid"],
                   space_guid=space_guid)

    @classmethod
    def get_list_via_organization(cls, organization_guid):
        response = api.api_get_organization_users(organization_guid)
        users = []
        for user_data in response:
            users.append(cls(guid=user_data["guid"], username=user_data["username"], roles=user_data["roles"],
                             organization_guid=organization_guid))
        return users

    @classmethod
    def get_list_via_space(cls, space_guid):
        response = api.api_get_space_users(space_guid)
        users = []
        for user_data in response:
            users.append(cls(guid=user_data["guid"], username=user_data["username"], roles=user_data["roles"],
                             organization_guid=user_data["org_guid"], space_guid=space_guid))
        return users

    def update_via_organization(self, new_roles=None):
        if new_roles is not None:
            self.roles = new_roles
        api.api_update_organization_user(self.organization_guid, self.guid, new_roles)

    def update_via_space(self, new_username=None, new_roles=None):
        if new_username is not None:
            self.username = new_username
        if new_roles is not None:
            self.roles = new_roles
        api.api_update_space_user(self.organization_guid, self.space_guid, self.guid, new_username, new_roles)

    def delete_via_organization(self):
        api.api_delete_organization_user(self.organization_guid, self.guid)

    def delete_via_space(self):
        api.api_delete_space_user(self.space_guid, self.organization_guid)


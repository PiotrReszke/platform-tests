import functools
import time

from test_utils import TEST_SETTINGS, get_config_value, get_admin_client
from test_utils.api_client import ConsoleClient, AppClient
import test_utils.api_calls.user_management_api_calls as api


__all__ = ["User"]


@functools.total_ordering
class User(object):
    TEST_EMAIL = TEST_SETTINGS["TEST_EMAIL"]
    TEST_EMAIL_FORM = TEST_EMAIL.replace('@', '+{}@')
    __ADMIN = None

    def __init__(self, guid, username, roles=None, organization_guid=None, space_guid=None, client_type=None,
                 password=None):
        self.guid = guid
        self.username = username
        self.roles = [] if roles is None else roles
        self.organizations_guid = [] if organization_guid is None else [organization_guid]
        self.spaces_guid = [] if space_guid is None else [space_guid]
        self._password = password
        if client_type is not None:
            self._app_client = client_type(self.username, self._password)

    def __repr__(self):
        return "{0} (username={1}, guid={2})".format(self.__class__.__name__, self.username, self.guid)

    def __eq__(self, other):
        return (self.username == other.username and self.guid == other.guid
                and sorted(self.roles) == sorted(other.roles)
                and sorted(self.organizations_guid) == sorted(other.organizations_guid)
                and sorted(self.spaces_guid) == sorted(other.spaces_guid))

    def __lt__(self, other):
        return self.guid < other.guid

    @property
    def app_client(self):
        return self._app_client

    @staticmethod
    def get_default_username(prefix="test-user-"):
        return prefix + str(time.time()) + "@mailinator.com"

    @classmethod
    def create_via_organization(cls, organization_guid, username=None, roles=None, client=None, client_type=None):
        client = client or get_admin_client()
        username = cls.get_default_username() if username is None else username
        response = api.api_create_organization_user(client, organization_guid, username, roles)
        return cls(guid=response["guid"], username=username, roles=roles, organization_guid=organization_guid,
                   client_type=client_type)

    @classmethod
    def create_via_space(cls, space_guid, organization_guid=None, username=None, roles=None, client=None):
        client = client or get_admin_client()
        username = cls.get_default_username() if username is None else username
        response = api.api_create_space_user(client, space_guid, username, organization_guid, roles)
        return cls(guid=response["guid"], username=username, roles=roles, organization_guid=response["org_guid"],
                   space_guid=space_guid)

    @classmethod
    def get_list_via_organization(cls, organization_guid, client=None):
        client = client or get_admin_client()
        response = api.api_get_organization_users(client, organization_guid)
        users = []
        for user_data in response:
            users.append(cls(guid=user_data["guid"], username=user_data["username"], roles=user_data["roles"],
                             organization_guid=organization_guid))
        return users

    @classmethod
    def get_list_via_space(cls, space_guid, client=None):
        client = client or get_admin_client()
        response = api.api_get_space_users(client, space_guid)
        users = []
        for user_data in response:
            users.append(cls(guid=user_data["guid"], username=user_data["username"], roles=user_data["roles"],
                             organization_guid=user_data["org_guid"], space_guid=space_guid))
        return users

    @classmethod
    def create_user_for_client(cls, org_guid, role, extension=None):
        username = cls.TEST_EMAIL_FORM.format(time.time() if extension is None else extension)
        roles = list(role.value)
        return cls.create_via_organization(org_guid, username, roles, client_type=ConsoleClient)

    def add_to_organization(self, organization_guid, roles, client=None):
        client = client or get_admin_client()
        api.api_create_organization_user(client, organization_guid, self.username, roles)

    def update_via_organization(self, new_roles=None, client=None):
        client = client or get_admin_client()
        if new_roles is not None:
            self.roles = new_roles
        api.api_update_organization_user(client, self.organizations_guid[0], self.guid, new_roles)

    def update_via_space(self, new_username=None, new_roles=None, client=None):
        client = client or get_admin_client()
        if new_username is not None:
            self.username = new_username
        if new_roles is not None:
            self.roles = new_roles
        api.api_update_space_user(client, self.organizations_guid[0], self.space_guid, self.guid, new_username,
                                  new_roles)

    def delete_via_organization(self, client=None):
        client = client or get_admin_client()
        api.api_delete_organization_user(client, self.organizations_guid[0], self.guid)

    def delete_via_space(self, client=None):
        client = client or get_admin_client()
        api.api_delete_space_user(client, self.space_guid, self.organizations_guid[0])

    @classmethod
    def get_admin(cls):
        if cls.__ADMIN is None:
            admin_guid = get_config_value("admin_guid")
            admin_username = get_config_value("admin_username")
            admin_password = TEST_SETTINGS["TEST_PASSWORD"]
            cls.__ADMIN = cls(guid=admin_guid, username=admin_username, client_type=AppClient, password=admin_password)
        return cls.__ADMIN

# fix deletion via org/space to delete from all org/space
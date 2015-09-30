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
import time

from test_utils import config, PlatformApiClient, platform_api_calls as api, cloud_foundry as cf, gmail_api, \
    JobFailedException, get_logger, UnexpectedResponseError
from . import Organization


__all__ = ["User"]

logger = get_logger("user")


@functools.total_ordering
class User(object):

    TEST_EMAIL = config.TEST_SETTINGS["TEST_EMAIL"]
    TEST_EMAIL_FORM = TEST_EMAIL.replace('@', '+{}@')
    __ADMIN = None
    ORG_ROLES = {
        "manager": {"managers"},
        "auditor": {"auditors"},
        "billing_manager": {"billing_managers"}
    }
    TEST_USERS = []

    def __init__(self, guid=None, username=None, password=None, org_roles=None, space_roles=None):
        self.guid, self.username, self.password = guid, username, password
        self.org_roles = org_roles or {}
        self.space_roles = space_roles or {}

    def __repr__(self):
        return "{0} (username={1}, guid={2})".format(self.__class__.__name__, self.username, self.guid)

    def __eq__(self, other):
        return self.username == other.username and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    def __hash__(self):
        return hash((self.guid, self.username))

    @classmethod
    def get_default_username(cls):
        return cls.TEST_EMAIL_FORM.format(time.time())

    @classmethod
    def api_onboard(cls, username=None, password="testPassw0rd", org_name=None, inviting_client=None):
        """Onboarding of a new user. Return new User and Organization objects."""
        username = cls.api_invite(username, inviting_client)
        code = gmail_api.get_invitation_code(username)
        return cls.api_register_after_onboarding(code, username, password, org_name)

    @classmethod
    def api_invite(cls, username=None, inviting_client=None):
        """Send invitation to a new user using inviting_client."""
        if username is None:
            username = User.get_default_username()
        api.api_invite_user(username, client=inviting_client)
        return username

    @classmethod
    def api_register_after_onboarding(cls, code, username, password="testPassw0rd", org_name=None):
        """Set password for new user and select name for their organization. Return objects for new user and org"""
        if org_name is None:
            org_name = Organization.get_default_name()
        client = PlatformApiClient.get_client(username)
        api.api_register_new_user(code, password, org_name, client=client)
        # need to obtain org guid (DPNG-2149)
        new_org = Organization.get_org_and_space_by_name(org_name=org_name)[0]
        Organization.TEST_ORGS.append(new_org)
        # need to obtain user's guid (DPNG-2149)
        org_users = cls.api_get_list_via_organization(org_guid=new_org.guid)
        new_user = next(u for u in org_users if u.username == username)
        new_user.password = password
        new_user.org_roles[new_org.guid] = ["managers"]  # user is an org manager in the organization they create
        cls.TEST_USERS.append(new_user)
        return new_user, new_org

    @classmethod
    def api_create_by_adding_to_organization(cls, org_guid, username=None, password="testPassw0rd",
                                             roles=ORG_ROLES["manager"], inviting_client=None):
        username = username or cls.get_default_username()
        api.api_add_organization_user(org_guid, username, roles, client=inviting_client)
        code = gmail_api.get_invitation_code(username)
        client = PlatformApiClient.get_client(username)
        api.api_register_new_user(code, password, client=client)
        org_users = cls.api_get_list_via_organization(org_guid=org_guid)
        new_user = next((user for user in org_users if user.username == username), None)
        if new_user is None:
            raise AssertionError("New user was not found in the organization")
        new_user.password = password
        cls.TEST_USERS.append(new_user)
        return new_user

    @classmethod
    def api_create_by_adding_to_space(cls, org_guid, space_guid, username=None, password="testPassw0rd",
                                      roles=("managers",), inviting_client=None):
        username = username or cls.get_default_username()
        api.api_add_space_user(org_guid, space_guid, username, roles, inviting_client)
        code = gmail_api.get_invitation_code(username)
        client = PlatformApiClient.get_client(username)
        api.api_register_new_user(code, password, client=client)
        space_users = cls.api_get_list_via_space(space_guid)
        new_user = next((user for user in space_users if user.username == username), None)
        new_user.password = password
        cls.TEST_USERS.append(new_user)
        return new_user

    @classmethod
    def api_get_list_via_organization(cls, org_guid, client=None):
        response = api.api_get_organization_users(org_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.org_roles[org_guid] = user_data["roles"]
            users.append(user)
        return users

    @classmethod
    def api_get_list_via_space(cls, space_guid, client=None):
        response = api.api_get_space_users(space_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.space_roles[space_guid] = user_data["roles"]
            users.append(user)
        return users

    def login(self):
        """Return a logged-in API client for this user."""
        client = PlatformApiClient.get_client(self.username)
        client.authenticate(self.password)
        return client

    def api_add_to_organization(self, org_guid, roles=ORG_ROLES["manager"], client=None):
        api.api_add_organization_user(org_guid, self.username, roles, client=client)
        self.org_roles[org_guid] = list(set(self.org_roles.get(org_guid, set())) | set(roles))

    def api_add_to_space(self, space_guid, org_guid, roles=("managers",), client=None):
        api.api_add_space_user(org_guid=org_guid, space_guid=space_guid, username=self.username,
                               roles=roles, client=client)
        self.space_roles[space_guid] = list(roles)

    def api_update_via_organization(self, org_guid, new_roles=None, client=None):
        api.api_update_organization_user(org_guid, self.guid, new_roles, client=client)
        self.org_roles[org_guid] = list(new_roles)

    def api_update_via_space(self, org_guid, space_guid, new_username=None, new_roles=None, client=None):
        api.api_update_space_user(org_guid, space_guid, self.guid, new_username, new_roles, client=client)
        if new_username is not None:
            self.username = new_username
        if new_roles is not None:
            self.space_roles[space_guid] = list(new_roles)

    def api_delete_from_organization(self, org_guid, client=None):
        api.api_delete_organization_user(org_guid, self.guid, client=client)

    def api_delete_from_space(self, space_guid, client=None):
        api.api_delete_space_user(space_guid, self.guid, client=client)

    @classmethod
    def get_admin(cls):
        """Return User object for admin user"""
        if cls.__ADMIN is None:
            users = User.cf_api_get_all_users()
            admin_username = config.get_config_value("admin_username")
            cls.__ADMIN = next(user for user in users if user.username == admin_username)
        return cls.__ADMIN

    @classmethod
    def _get_user_list_from_cf_api_response(cls, response):
        users = []
        for user_data in response:
            user = cls(username=user_data["entity"].get("username"), guid=user_data["metadata"].get("guid"))
            users.append(user)
        return users

    @classmethod
    def cf_api_get_all_users(cls):
        response = cf.cf_api_get_all_users()
        return cls._get_user_list_from_cf_api_response(response)

    @classmethod
    def cf_api_get_list_in_organization(cls, org_guid, space_guid=None):
        response = cf.cf_api_get_organization_space_users(org_guid=org_guid, space_guid=space_guid)
        return cls._get_user_list_from_cf_api_response(response)

    def cf_api_delete(self, async=True):
        try:
            cf.cf_api_delete_user(self.guid, async=async)
        except UnexpectedResponseError as e:
            if "CF-UserNotFound" in e.error_message:
                logger.warning("User {} was not found".format(self.guid))
            else:
                raise

    @classmethod
    def cf_api_delete_users_from_list(cls, user_list, async=True):
        failed_to_delete = []
        for user in user_list:
            try:
                user.cf_api_delete(async=async)
            except JobFailedException:
                failed_to_delete.append(user)
                logger.exception("Could not delete {}\n".format(user))
        return failed_to_delete

    @classmethod
    def cf_api_tear_down_test_users(cls):
        """Use this method in tearDown and tearDownClass."""
        cls.TEST_USERS = cls.cf_api_delete_users_from_list(cls.TEST_USERS, async=False)

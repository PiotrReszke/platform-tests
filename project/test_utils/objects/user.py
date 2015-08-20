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

import datetime
import functools
import re
import time

from test_utils import config
from test_utils.api_client import PlatformApiClient
import test_utils.platform_api_calls as api
from test_utils.objects import Organization
import test_utils.cli.cloud_foundry as cf


__all__ = ["User"]


@functools.total_ordering
class User(object):
    TEST_EMAIL = config.TEST_SETTINGS["TEST_EMAIL"]
    TEST_EMAIL_FORM = TEST_EMAIL.replace('@', '+{}@')
    __ADMIN = None

    def __init__(self, guid=None, username=None, password=None):
        self.guid, self.username, self.password = guid, username, password
        self.org_roles = {}
        self.space_roles = {}

    def __repr__(self):
        return "{0} (username={1}, guid={2})".format(self.__class__.__name__, self.username, self.guid)

    def __eq__(self, other):
        return self.username == other.username and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid

    @classmethod
    def get_default_username(cls):
        return cls.TEST_EMAIL_FORM.format(time.time())

    @classmethod
    def api_onboard_and_login(cls, username=None, password="testPassw0rd", org_name=None, inviting_client=None):
        """Send invite to a new user who then creates an account and an organization. Return new user and API client."""
        org_name = org_name or "test_org_{}".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        username = username or cls.get_default_username()
        code = cls.api_invite(username, inviting_client)
        return cls.api_register_and_login(code, username, password, org_name)

    @classmethod
    def api_invite(cls, username=None, inviting_client=None):
        """Send invitation to a new user using inviting_client. Return invitation code."""
        username = username or cls.get_default_username()
        response = api.api_invite_user(username, client=inviting_client)
        return re.search("([a-z]|[0-9]|-)*$", response["details"]).group(0)

    @classmethod
    def api_register_and_login(cls, code, username, password="testPassw0rd", org_name=None):
        """Set password for new user and select name for their organization"""
        org_name = org_name or Organization.get_default_name()
        client = PlatformApiClient.get_client(username)
        api.api_register_new_user(code, password, org_name, client=client)
        new_org = Organization.get_org_and_space_by_name(org_name=org_name)[0]
        Organization.TEST_ORGS.append(new_org)
        new_user = cls.api_get_list_via_organization(new_org.guid)[0]  # need to obtain user's guid
        new_user.password = password
        new_user.org_roles[new_org.guid] = ["managers"]  # user is an org manager in the organization they create
        client.authenticate(password)
        return new_user, new_org, client

    @classmethod
    def api_create_by_adding_to_organization(cls, organization_guid, username=None, roles=None, client=None):
        username = username or cls.get_default_username()
        response = api.api_add_organization_user(organization_guid, username, roles, client=client)
        user = cls(guid=response["guid"], username=username)
        user.org_roles[organization_guid] = roles
        return user

    @classmethod
    def api_get_list_via_organization(cls, organization_guid, client=None):
        response = api.api_get_organization_users(organization_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.org_roles[organization_guid] = user_data["roles"]
            users.append(user)
        return users

    @classmethod
    def api_get_list_via_space(cls, space_guid, client=None):
        response = api.api_get_space_users(space_guid, client=client)
        users = []
        for user_data in response:
            user = cls(guid=user_data["guid"], username=user_data["username"])
            user.space_roles[space_guid] = response["roles"]
            users.append(user)
        return users

    def api_add_to_organization(self, org_guid, roles=("managers",), client=None):
        self.org_roles[org_guid] = roles
        api.api_add_organization_user(org_guid, self.username, roles, client=client)

    def api_add_to_space(self, space_guid, org_guid, roles=("managers",), client=None):
        api.api_create_space_user(org_guid=org_guid, space_guid=space_guid, username=self.username,
                                  roles=roles, client=client)
        self.space_roles[space_guid] = roles

    def api_update_via_organization(self, org_guid, new_roles=None, client=None):
        self.org_roles[org_guid] = new_roles
        api.api_update_organization_user(org_guid, self.guid, new_roles, client=client)

    def api_update_via_space(self, org_guid, space_guid, new_username=None, new_roles=None, client=None):
        if new_username is not None:
            self.username = new_username
        if new_roles is not None:
            self.space_roles[space_guid] = new_roles
        api.api_update_space_user(org_guid, space_guid, self.guid, new_username, new_roles, client=client)

    def api_delete_via_organization(self, org_guid, client=None):
        api.api_delete_organization_user(org_guid, self.guid, client=client)

    def api_delete_via_space(self, space_guid, client=None):
        api.api_delete_space_user(space_guid, self.guid, client=client)

    @classmethod
    def get_admin(cls):
        """Return User object for admin user"""
        if cls.__ADMIN is None:
            testers_sandbox = Organization.get_org_and_space_by_name(org_name="testers-sandbox")[0]
            users = cls.api_get_list_via_organization(testers_sandbox.guid)
            admin_username = config.get_config_value("admin_username")
            cls.__ADMIN = next(user for user in users if user.username == admin_username)
        return cls.__ADMIN

    @classmethod
    def cf_api_get_list_in_organization(cls, org_guid):
        response = cf.cf_api_get_organization_users(org_guid)
        users = []
        for user_data in response:
            user = cls(username=user_data["entity"]["username"], guid=user_data["metadata"]["guid"])
            users.append(user)
        return users

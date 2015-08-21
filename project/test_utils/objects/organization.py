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
from datetime import datetime

from test_utils import config, get_logger, get_admin_client, get_config_value
import test_utils.api_calls.metrics_provider_api_calls as metrics_api
import test_utils.api_calls.user_management_api_calls as api
from test_utils.objects import Space, User
import test_utils.cli.cloud_foundry as cf


__all__ = ["Organization"]


logger = get_logger("organization")


@functools.total_ordering
class Organization(object):

    NAME_PREFIX = "test_org_"
    TEST_ORGS = []
    TEST_EMAIL = config.TEST_SETTINGS["TEST_EMAIL"]
    TEST_EMAIL_FORM = TEST_EMAIL.replace('@', '+{}@')

    def __init__(self, name, guid, spaces=None):
        self.name = name
        self.guid = guid
        self.spaces = [] if spaces is None else spaces
        self.metrics = {}

    def __repr__(self):
        return "{0} (name={1}, guid={2}, spaces={3})".format(self.__class__.__name__, self.name, self.guid, self.spaces)

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid and sorted(self.spaces) == sorted(other.spaces)

    def __lt__(self, other):
        return self.guid < other.guid

    # -------------------------------- platform api -------------------------------- #

    @classmethod
    def create(cls, name=None, space_names=(), client=None):
        client = client or get_admin_client()
        if name is None:
            name = cls.NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        response = api.api_create_organization(client, name)
        response = response.strip('"')  # guid is returned together with quotation marks
        org = cls(name=name, guid=response)
        cls.TEST_ORGS.append(org)
        for space_name in space_names:
            Space.api_create(org=org, name=space_name, client=client)
        return org

    @classmethod
    def get_list(cls, client=None):
        client = client or get_admin_client()
        response = api.api_get_organizations(client)
        organizations = []
        for organization_data in response:
            spaces = [Space(name=space_data["name"], guid=space_data["guid"])
                      for space_data in organization_data["spaces"]]
            org = cls(name=organization_data["name"], guid=organization_data["guid"], spaces=spaces)
            organizations.append(org)
        return organizations

    @classmethod
    def api_delete_test_orgs(cls):
        while len(cls.TEST_ORGS) > 0:
            org = cls.TEST_ORGS.pop()
            org.api_delete(with_spaces=True)

    @classmethod
    def get_org_and_space(cls, org_name=None, space_name=None, client=None):
        client = client or get_admin_client()
        response = api.api_get_organizations(client)
        organization = space = None
        if org_name is not None:
            org_details = next(org for org in response if org.name == org_name)
            organization = cls(name=org_details["name"], guid=org_details["guid"])
        if space_name is not None:
            space_details = next(space for space in org_details["spaces"] if space.name == space_name)
            space = Space(name=space_details["name"], guid=space_details["guid"])
        return organization, space

    def rename(self, new_name, client=None):
        client = client or get_admin_client()
        self.name = new_name
        return api.api_rename_organization(client, self.guid, new_name)

    def api_delete(self, with_spaces=False, client=None):
        client = client or get_admin_client()
        if self in self.TEST_ORGS:
            self.TEST_ORGS.remove(self)
        if with_spaces:
            while len(self.spaces) > 0:
                space = self.spaces.pop()
                space.delete_associations()
                space.api_delete()
        api.api_delete_organization(client, self.guid)

    def add_admin(self, roles=("managers",)):
        """Add admin user to the organization"""
        admin_username = get_config_value("admin_username")
        User.create_via_organization(self.guid, admin_username, roles)

    # @classmethod
    # def invite(cls, email=None, client=get_admin_client()):
    #     """Invite user - return invitation code"""
    #     if email is None:
    #         email = cls.TEST_EMAIL_FORM.format(time.time())
    #     response = api.api_invite_user(client, email)
    #     code_link = response["details"]
    #     code_id = code_link.find("code=") + len("code=")
    #     return email, code_link[code_id:]
    #
    #
    # @classmethod
    # def onboard(cls, code, org_name=None, password=None, client=get_unauthorized_client()):
    #     """Answer onboarding invitation"""
    #     if org_name is None:
    #         org_name = cls.NAME_PREFIX + str(time.time())
    #     if password is None:
    #         password = "nieczesc"
    #     response = api.api_register_org_and_user(client, code, org_name, password)
    #     print(response)
    #     org = cls(name=org_name, guid=response["guid"]) # how to obtain org guid ?
    #     cls.TEST_ORGS.append(org)
    #     return org

    def api_get_metrics(self, client=None):
        client = client or get_admin_client()
        response = metrics_api.api_get_org_metrics(client, self.guid)
        self.metrics = {}
        for response_key in ["appsDown", "appsRunning", "datasetCount", "domainsUsage", "memoryUsageAbsolute",
                             "privateDatasets", "publicDatasets", "serviceUsage", "totalUsers"]:
            self.metrics[response_key] = response.get(response_key)
            if self.metrics[response_key] is None:
                logger.warning("Missing metrics in response: {}".format(response_key))
        for response_key in ["domainsUsagePercent", "memoryUsage", "serviceUsagePercent"]:
            if response.get(response_key) is None:
                logger.warning("Missing metrics in response: {}".format(response_key))
            self.metrics[response_key] = response[response_key]["numerator"] / response[response_key]["denominator"]

    def api_get_spaces(self, client=None):
        client = client or get_admin_client()
        response = api.api_get_spaces_in_org(client, org_guid=self.guid)
        spaces = []
        for space_data in response["resources"]:
            spaces.append(Space(name=space_data["entity"]["name"], guid=space_data["metadata"]["guid"]))
        return spaces

    # -------------------------------- cf api -------------------------------- #

    def cf_api_get_spaces(self):
        response = cf.cf_api_get_organization_spaces(self.guid)
        spaces = []
        for space_data in response:
            spaces.append(Space(name=space_data["entity"]["name"], guid=space_data["metadata"]["guid"]))
        return spaces

    def cf_api_get_apps_and_services(self, client=None):
        spaces = self.api_get_spaces(client=client)
        org_apps = []
        org_services = []
        for space in spaces:
            apps, services = space.cf_api_get_space_summary()
            org_apps.extend(apps)
            org_services.extend(services)
        return org_apps, org_services

    def cf_api_get_users(self):
        response = cf.cf_api_get_organization_users(self.guid)
        users = []
        for user_data in response:
            users.append(User(username=user_data["entity"]["username"], guid=user_data["metadata"]["guid"]))
        return users

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

from test_utils import get_logger
import test_utils.cli.cloud_foundry as cf
from test_utils.objects import Space
import test_utils.platform_api_calls as api



__all__ = ["Organization"]


logger = get_logger("organization")


@functools.total_ordering
class Organization(object):

    TEST_ORGS = []

    def __init__(self, name, guid=None, spaces=None):
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

    @staticmethod
    def get_default_name():
        return "test_org_{}".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f'))

    # -------------------------------- platform api -------------------------------- #

    @classmethod
    def create(cls, name=None, space_names=(), client=None):
        """If you pass a tuple of space names, spaces with those names are created in the organization."""
        name = name or cls.get_default_name()
        response = api.api_create_organization(name, client=client)
        org = cls(name=name, guid=response)
        cls.TEST_ORGS.append(org)
        for space_name in space_names:
            Space.api_create(org=org, name=space_name, client=client)
        return org

    @classmethod
    def api_get_list(cls, client=None):
        response = api.api_get_organizations(client=client)
        organizations = []
        for organization_data in response:
            spaces = [Space(name=space_data["name"], guid=space_data["guid"])
                      for space_data in organization_data["spaces"]]
            org = cls(name=organization_data["name"], guid=organization_data["guid"], spaces=spaces)
            organizations.append(org)
        return organizations

    @classmethod
    def api_tear_down_test_orgs(cls):
        if any([org.guid is None for org in cls.TEST_ORGS]):  # clean up also those orgs whose guid was not set
            test_org_names = [org.name for org in cls.TEST_ORGS]
            platform_orgs = cls.api_get_list()
            cls.TEST_ORGS = [org for org in platform_orgs if org.name in test_org_names]
        while len(cls.TEST_ORGS) > 0:
            org = cls.TEST_ORGS.pop()
            org.api_delete(with_spaces=True)

    @classmethod
    def get_org_and_space_by_name(cls, org_name, space_name=None, client=None):
        """Return organization and space objects for existing org and space"""
        response = api.api_get_organizations(client=client)
        org_details = next(org for org in response if org["name"] == org_name)
        organization = cls(name=org_details["name"], guid=org_details["guid"])
        space = None
        if space_name is not None:
            space_details = next(space for space in org_details["spaces"] if space["name"] == space_name)
            space = Space(name=space_details["name"], guid=space_details["guid"])
        return organization, space

    def rename(self, new_name, client=None):
        self.name = new_name
        return api.api_rename_organization(self.guid, new_name, client=client)

    def api_delete(self, with_spaces=False, client=None):
        if self in self.TEST_ORGS:
            self.TEST_ORGS.remove(self)
        if with_spaces:
            spaces = self.api_get_spaces()  # when organization is created, a default space is added automatically
            while len(spaces) > 0:
                space = spaces.pop()
                space.delete_associations()
                space.api_delete()
        api.api_delete_organization(self.guid, client=client)

    def api_get_metrics(self, client=None):
        response = api.api_get_org_metrics(self.guid, client=client)
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
        response = api.api_get_spaces_in_org(org_guid=self.guid, client=client)
        spaces = []
        for space_data in response:
            space = Space(name=space_data["entity"]["name"], guid=space_data["metadata"]["guid"], org_guid=self.guid)
            spaces.append(space)
        return spaces

    # -------------------------------- cf api -------------------------------- #

    def cf_api_get_spaces(self):
        response = cf.cf_api_get_organization_spaces(self.guid)
        spaces = []
        for space_data in response:
            space = Space(space_data["entity"]["name"], space_data["metadata"]["guid"], self.guid)
            spaces.append(space)
        return spaces

    def cf_api_get_apps_and_services(self, client=None):
        """Return aggregated space summary for all spaces in the organization"""
        spaces = self.api_get_spaces(client=client)
        org_apps = []
        org_services = []
        for space in spaces:
            apps, services = space.cf_api_get_space_summary()
            org_apps.extend(apps)
            org_services.extend(services)
        return org_apps, org_services

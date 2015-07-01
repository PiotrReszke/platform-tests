import time

import test_utils.user_management.api_calls as api


class Organization(object):

    NAME_PREFIX = "test-org-"
    TEST_ORGS = []

    def __init__(self, name, guid, spaces=None):
        self.name = name
        self.guid = guid
        self.spaces = [] if spaces is None else spaces

    def __repr__(self):
        return "{0} (name={1}, guid={2}, spaces={3})".format(self.__class__.__name__, self.name, self.guid, self.spaces)

    def __eq__(self, other):
        return (self.name == other.name and self.guid == other.guid and sorted(self.spaces) == sorted(other.spaces))

    def __cmp__(self, other):
        if self.guid < other.guid:
            return -1
        if self.guid > other.guid:
            return 1
        return 0

    @classmethod
    def create(cls, name=None):
        if name is None:
            name = cls.NAME_PREFIX + str(time.time())
        response = api.api_create_organization(name)
        response = response.strip('"') # guid is returned together with quotation marks
        org = cls(name=name, guid=response)
        cls.TEST_ORGS.append(org)
        return org

    @classmethod
    def get_list(cls):
        response = api.api_get_organizations()
        organizations = []
        for organization_data in response:
            spaces = [Space(name=space_data["name"], guid=space_data["guid"])
                      for space_data in organization_data["spaces"]]
            org = cls(name=organization_data["name"], guid=organization_data["guid"], spaces=spaces)
            organizations.append(org)
        return organizations

    @classmethod
    def delete_test_orgs(cls):
        while len(cls.TEST_ORGS) > 0:
            org = cls.TEST_ORGS[0]
            org.delete()

    def rename(self, new_name):
        self.name = new_name
        return api.api_rename_organization(self.guid, new_name)

    def delete(self):
        self.TEST_ORGS.remove(self)
        return api.api_delete_organization(self.guid)


class Space(object):

    def __init__(self, name, guid):
        self.name = name
        self.guid = guid

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

    def __eq__(self, other):
        return (self.name == other.name and self.guid == other.guid)

    def __cmp__(self, other):
        if self.guid < other.guid:
            return -1
        if self.guid > other.guid:
            return 1
        return 0



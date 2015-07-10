import functools
import time

from test_utils import config
import test_utils.api_calls.user_management_api_calls as api
from test_utils.objects.user import get_admin_user, get_admin_client



__all__ = ["Organization", "Space"]


@functools.total_ordering
class Organization(object):

    NAME_PREFIX = "test-org-"
    TEST_ORGS = []
    TEST_EMAIL = config.TEST_SETTINGS["TEST_EMAIL"]
    TEST_EMAIL_FORM = TEST_EMAIL.replace('@', '+{}@')

    def __init__(self, name, guid, spaces=None):
        self.name = name
        self.guid = guid
        self.spaces = [] if spaces is None else spaces

    def __repr__(self):
        return "{0} (name={1}, guid={2}, spaces={3})".format(self.__class__.__name__, self.name, self.guid, self.spaces)

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid and sorted(self.spaces) == sorted(other.spaces)

    def __lt__(self, other):
        return self.guid < other.guid

    @classmethod
    def create(cls, name=None, client=None):
        client = client or get_admin_client()
        if name is None:
            name = cls.NAME_PREFIX + str(time.time())
        response = api.api_create_organization(client, name)
        response = response.strip('"')  # guid is returned together with quotation marks
        org = cls(name=name, guid=response)
        cls.TEST_ORGS.append(org)
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
    def delete_test_orgs(cls):
        while len(cls.TEST_ORGS) > 0:
            org = cls.TEST_ORGS[0]
            org.delete()

    def rename(self, new_name, client=None):
        client = client or get_admin_client()
        self.name = new_name
        return api.api_rename_organization(client, self.guid, new_name)

    def delete(self, client=None):
        client = client or get_admin_client()
        self.TEST_ORGS.remove(self)
        return api.api_delete_organization(client, self.guid)

    def add_admin(self, roles=("managers",)):
        """Add admin user to the organization"""
        admin = get_admin_user()
        admin.add_to_organization(self.guid, list(roles))

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


@functools.total_ordering
class Space(object):

    def __init__(self, name, guid):
        self.name = name
        self.guid = guid

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

    def __eq__(self, other):
        return self.name == other.name and self.guid == other.guid

    def __lt__(self, other):
        return self.guid < other.guid



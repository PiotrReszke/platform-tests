from test_utils import ApiTestCase, cleanup_after_failed_setup
from test_utils import Organization, User


class TestOrganizationUsers(ApiTestCase):

    @classmethod
    @cleanup_after_failed_setup(Organization.delete_test_orgs)
    def setUpClass(self):
        self.organization = Organization.create()

    def test_create_organization_user(self):
        expected_user = User.create_via_organization(self.organization.guid)
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)

    def test_create_organization_user_with_role(self):
        """Create a user with each of the roles allowed"""
        for role in ["managers", "auditors", "billing_managers"]:
            with self.subTest(role=role):
                expected_user = User.create_via_organization(self.organization.guid, roles=[role])
                users = User.get_list_via_organization(self.organization.guid)
                self.assertInList(expected_user, users)

    def test_create_organization_user_two_roles(self):
        expected_user = User.create_via_organization(self.organization.guid, roles=["managers", "auditors"])
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)

    def test_create_organization_user_all_roles(self):
        expected_user = User.create_via_organization(self.organization.guid, roles=["managers", "auditors", "billing_managers"])
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)

    def test_create_organization_user_incorrect_role(self):
        self.assertRaisesUnexpectedResponse(400, None, User.create_via_organization,
                                            organization_guid=self.organization.guid, roles=["i-don't-exist"])

    def test_update_organization_user_add_role(self):
        roles = ["managers"]
        new_roles = ["managers", "auditors"]
        expected_user = User.create_via_organization(self.organization.guid, roles=roles)
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)
        expected_user.update_via_organization(new_roles=new_roles)
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)

    def test_update_organization_user_remove_role(self):
        roles = ["managers", "billing_managers"]
        new_roles = ["managers"]
        expected_user = User.create_via_organization(self.organization.guid, roles=roles)
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)
        expected_user.update_via_organization(new_roles=new_roles)
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)

    def test_update_organization_user_change_role(self):
        roles = ["managers"]
        new_roles = ["auditors"]
        expected_user = User.create_via_organization(self.organization.guid, roles=roles)
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)
        expected_user.update_via_organization(new_roles=new_roles)
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)

    def test_delete_organization_user(self):
        expected_user = User.create_via_organization(self.organization.guid)
        users = User.get_list_via_organization(self.organization.guid)
        self.assertInList(expected_user, users)
        expected_user.delete_via_organization()
        users = User.get_list_via_organization(self.organization.guid)
        self.assertNotInList(expected_user, users)




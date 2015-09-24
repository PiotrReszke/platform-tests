import time
import unittest

from test_utils import config, gmail_api, get_logger, ApiTestCase, platform_api_calls as api
from objects import User, Organization


logger = get_logger("test onboarding")


class Onboarding(ApiTestCase):
    EXPECTED_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
    CLIENT_ID = "intel.data.tests@gmail.com"

    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()

    def _assert_message_correct(self, message_subject, message_content):
        expected_link = "https://console.{}/new-account".format(config.TEST_SETTINGS["TEST_ENVIRONMENT"])
        message_link = gmail_api.get_link_from_message(message_content)
        correct_link = (expected_link in message_link,
                        "Link to create account: {}, expected: {}".format(message_link, expected_link))
        expected_inviting_user = config.TEST_SETTINGS["TEST_USERNAME"]
        correct_inviting_user = (expected_inviting_user in message_content,
                                 "Inviting user {} was not found in message content.".format(expected_inviting_user))
        correct_subject = (self.EXPECTED_EMAIL_SUBJECT in message_subject,
                           "Message subject {}. Expected: {}".format(message_subject, self.EXPECTED_EMAIL_SUBJECT))
        error_message = [error_msg for condition, error_msg in [correct_link, correct_inviting_user, correct_subject]
                         if not condition]
        self.assertTrue(all((correct_link[0], correct_inviting_user[0], correct_subject[0])), error_message)

    def _assert_user_received_messages(self, username, number_of_messages):
        time.sleep(30)
        messages = gmail_api.get_messages(recipient=username)
        self.assertEqual(len(messages), number_of_messages, "There are {} messages for {}. Expected: {}"
                         .format(len(messages), username, number_of_messages))
        for message in messages:
            self._assert_message_correct(message["subject"], message["content"])

    def test_simple_onboarding(self):
        username = User.api_invite()
        self._assert_user_received_messages(username, 1)
        code = gmail_api.get_invitation_code(username)
        user, organization = User.api_register_after_onboarding(code, username)
        organizations = Organization.api_get_list()
        self.assertInList(organization, organizations, "New organization was not found")
        users = User.api_get_list_via_organization(org_guid=organization.guid)
        self.assertInList(user, users, "Invited user was not found in new organization")

    @unittest.expectedFailure
    def test_invite_existing_user(self):
        """DPNG-2364 Onboarding existing user sends a new email invitation"""
        user, organization = User.api_onboard()
        self.assertRaisesUnexpectedResponse(409, "", User.api_invite, user.username)
        # checking for one message, because there should be one already after user creation
        self._assert_user_received_messages(user.username, 1)

    @unittest.expectedFailure
    def test_non_admin_user_invites_another_user(self):
        """DPNG-2366 Non admin user invites another user - http 500"""
        non_admin_user, _ = User.api_onboard()
        non_admin_user_client = non_admin_user.login()
        username = User.get_default_username()
        self.assertRaisesUnexpectedResponse(403, "", User.api_invite, username, inviting_client=non_admin_user_client)
        self._assert_user_received_messages(username, 0)

    def test_create_account_with_invalid_code(self):
        username = User.get_default_username()
        self.assertRaisesUnexpectedResponse(403, "", User.api_register_after_onboarding,
                                            "xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", username)

    def test_use_same_activation_code_twice(self):
        username = User.api_invite()
        code = gmail_api.get_invitation_code(username)
        User.api_register_after_onboarding(code, username)
        self.assertRaisesUnexpectedResponse(403, "", User.api_register_after_onboarding, code, username)

    @unittest.expectedFailure
    def test_invite_user_with_non_email_username(self):
        """DPNG-2272 Attempt to add user with incorrect e-mail address results in Intenternal Server Error"""
        username = "non_mail_username"
        self.assertRaisesUnexpectedResponse(400, "", User.api_invite, username)

    @unittest.expectedFailure
    def test_register_user_without_password(self):
        """DPNG-2367 Registration without password - http 500"""
        username = User.api_invite()
        code = gmail_api.get_invitation_code(username)
        self.assertRaisesUnexpectedResponse(400, "", User.api_register_after_onboarding, code, username, "")

    @unittest.skip("Getting all users list takes too long")
    def test_user_registers_already_existing_organization(self):
        existing_org = Organization.api_create()
        username = User.api_invite()
        code = gmail_api.get_invitation_code(username)
        self.assertRaisesUnexpectedResponse(400, "", User.api_register_after_onboarding, code, username,
                                            org_name=existing_org.name)
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotInList(username, username_list, "User was created")

    @unittest.expectedFailure
    def test_user_registers_with_no_organization_name(self):
        """DPNG-2458 It's possible to create user without organization after onboarding"""
        username = User.api_invite()
        code = gmail_api.get_invitation_code(username)
        self.assertRaisesUnexpectedResponse(400, "Bad Request", api.api_register_new_user, code=code,
                                            password="testPassw0rd")

    def test_invite_user_twice_and_try_to_register_with_latest_message(self):
        username = User.api_invite()
        User.api_invite(username)
        code = gmail_api.get_code_from_latest_message(username)
        user, org = User.api_register_after_onboarding(code, username)
        org_users = User.api_get_list_via_organization(org.guid)
        self.assertInList(user, org_users, "User has not been created.")

    @unittest.skip
    def test_check_invited_user_in_cf(self):
        user, _ = User.api_onboard()
        user_list = User.cf_api_get_all_users()
        self.assertInList(user, user_list, "User was not found in cf")
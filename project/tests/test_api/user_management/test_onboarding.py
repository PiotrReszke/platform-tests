import unittest
import re
import time

from test_utils import config, gmail_api, get_logger, ApiTestCase, platform_api_calls as api, get_test_name
from objects import User, Organization


logger = get_logger("test onboarding")


class Onboarding(ApiTestCase):
    EXPECTED_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
    CLIENT_ID = "intel.data.tests@gmail.com"
    SENDER_PATTERN = "TrustedAnalytics <support@{}>"

    @classmethod
    def setUpClass(cls):
        cls.test_org = Organization.api_create()

    @classmethod
    def tearDownClass(cls):
        User.cf_api_tear_down_test_users()
        User.api_tear_down_test_invitations()
        Organization.cf_api_tear_down_test_orgs()

    def _assert_message_correct(self, message_subject, message_content, message_sender):
        self.step("Check that the e-mail invitation message is correct")
        code = gmail_api.extract_code_from_message(message_content)

        expected_link_pattern = '"https?://console.{}/new-account\?code={}"'.format(config.CONFIG["domain"], code)
        message_link = gmail_api.get_link_from_message(message_content)
        correct_link = (re.match(expected_link_pattern, message_link),
                        "Link to create account: {}, expected pattern: {}".format(message_link, expected_link_pattern))

        expected_inviting_user = config.CONFIG["admin_username"]
        correct_inviting_user = (expected_inviting_user in message_content,
                                 "Inviting user {} was not found in message content.".format(expected_inviting_user))

        correct_subject = (self.EXPECTED_EMAIL_SUBJECT in message_subject,
                           "Message subject {}. Expected: {}".format(message_subject, self.EXPECTED_EMAIL_SUBJECT))

        expected_sender = self.SENDER_PATTERN.format(config.CONFIG["domain"])
        correct_sender = (expected_sender in message_sender,
                          "Message sender {}. Expected: {}".format(message_sender, expected_sender))

        error_message = [error_msg for condition, error_msg in
                         [correct_link, correct_inviting_user, correct_subject, correct_sender] if not condition]
        self.assertTrue(all((correct_link[0], correct_inviting_user[0], correct_subject[0])), error_message)

    def _assert_user_received_messages(self, username, number_of_messages):
        self.step("Check that the new user received {} e-mail message(s)".format(number_of_messages))
        if number_of_messages == 0:
            time.sleep(60)  # waiting 60 sek to ensure that we will notice all messages that are about to came
            self.assertFalse(gmail_api.is_there_any_messages_to(username),
                             "There are some messages for {} but none was expected.".format(username))

        else:
            messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=number_of_messages)
            self.assertEqual(len(messages), number_of_messages, "There are {} messages for {}. Expected: {}"
                             .format(len(messages), username, number_of_messages))
            for message in messages:
                self._assert_message_correct(message["subject"], message["content"], message["sender"])

    def test_simple_onboarding(self):
        self.step("Send an invite to a new user")
        username = User.api_invite()
        messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=1)
        self.assertEqual(len(messages), 1, "There are {} messages for {}. Expected: 1".format(len(messages), username))
        message = messages[0]
        self._assert_message_correct(message["subject"], message["content"], message["sender"])
        code = gmail_api.extract_code_from_message(message["content"])
        self.step("Register the new user")
        user, organization = User.api_register_after_onboarding(code, username)
        self.step("Check that the user and their organization exist")
        organizations = Organization.api_get_list()
        self.assertInList(organization, organizations, "New organization was not found")
        self.assert_user_in_org_and_roles(user, organization.guid, User.ORG_ROLES["manager"])

    def test_cannot_invite_existing_user(self):
        """DPNG-2364 Onboarding existing user sends a new email invitation"""
        self.step("Invite a test user. The new user registers.")
        user, organization = User.api_onboard()
        self.step("Check that sending invitation to the same user causes an error.")
        self.assertRaisesUnexpectedResponse(409, "User {} already exists".format(user.username),
                                            User.api_invite, user.username)

    def test_non_admin_user_cannot_invite_another_user(self):
        """DPNG-2366 Non admin user invites another user - http 500"""
        self.step("Create a test user")
        non_admin_user = User.api_create_by_adding_to_organization(org_guid=self.test_org.guid)
        non_admin_user_client = non_admin_user.login()
        self.step("Check an error is returned when non-admin tries to onboard another user")
        username = get_test_name(email=True)
        self.assertRaisesUnexpectedResponse(403, "Access is denied", User.api_invite, username,
                                            inviting_client=non_admin_user_client)
        self._assert_user_received_messages(username, 0)

    def test_cannot_create_an_account_with_invalid_code(self):
        self.step("An error is returned when user registers with invalid code")
        username = get_test_name(email=True)
        self.assertRaisesUnexpectedResponse(403, "", User.api_register_after_onboarding,
                                            "xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", username)

    def test_cannot_use_the_same_activation_code_twice(self):
        self.step("Invite a user")
        username = User.api_invite()
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("The new user registers")
        User.api_register_after_onboarding(code, username)
        self.step("Check that error is returned when the user tries to use code twice")
        self.assertRaisesUnexpectedResponse(403, "", User.api_register_after_onboarding, code, username)

    def test_invite_user_with_non_email_username(self):
        """DPNG-2625 Onboarding user with invalid e-mail as username results in Internal Server Error"""
        self.step("Check that passing invalid email results in error")
        username = "non_mail_username"
        self.assertRaisesUnexpectedResponse(409, "That email address is not valid", User.api_invite, username)

    def test_user_cannot_register_without_password(self):
        """DPNG-2367 Registration without password - http 500"""
        self.step("Invite a new user")
        username = User.api_invite()
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Check that an error is returned when the user tries to register without a password")
        self.assertRaisesUnexpectedResponse(400, "Password cannot be empty", api.api_register_new_user, code=code,
                                            org_name=get_test_name())
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotInList(username, username_list, "User was created")

    def test_user_cannot_register_already_existing_organization(self):
        self.step("Invite a new user")
        username = User.api_invite()
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Check that an error is returned when the user registers with an already-existing org name")
        self.assertRaisesUnexpectedResponse(409, "Organization \\\"{}\\\" already exists".format(self.test_org.name),
                                            User.api_register_after_onboarding, code, username,
                                            org_name=self.test_org.name)
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotInList(username, username_list, "User was created")

    def test_user_cannot_register_with_no_organization_name(self):
        """DPNG-2458 It's possible to create user without organization after onboarding"""
        self.step("Invite a new user")
        username = User.api_invite()
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Check that an error is returned when user registers without passing an org name")
        self.assertRaisesUnexpectedResponse(400, "Bad Request", api.api_register_new_user, code=code,
                                            password="testPassw0rd")
        self.step("Check that the user was not created")
        username_list = [user.username for user in User.cf_api_get_all_users()]
        self.assertNotInList(username, username_list, "User was created")


class PendingInvitations(ApiTestCase):

    def test_add_new_pending_invitation(self):
        self.step("Invite new user")
        username = User.api_invite()
        self.step("Check that the user is in the pending invitation list")
        self.assertInListWithRetry(username, User.api_get_pending_invitations)

    def test_accepting_invitation_deletes_it_from_pending_list(self):
        self.step("Invite new user")
        username = User.api_invite()
        self.step("Get registration code from received message")
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Register user with the received code")
        User.api_register_after_onboarding(code, username)
        self.step("Check that invitation is no longer present in pending invitation list")
        self.assertNotInListWithRetry(username, User.api_get_pending_invitations)

    def test_add_new_pending_invitation_twice_for_the_same_user(self):
        self.step("Send invitation two times for a single user")
        username = User.api_invite()
        User.api_invite(username=username)
        invitation_list = User.api_get_pending_invitations()
        self.step("Check that there is only one invitation for the user")
        self.assertEqual(invitation_list.count(username), 1, "More than one invitation for user {}".format(username))

    def test_resend_pending_invitation(self):
        self.step("Invite new user")
        username = User.api_invite()
        self.step("Check that the user received the message")
        messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=1)
        self.assertEqual(len(messages), 1)
        self.step("Resend invitation")
        User.api_resend_user_invitation(username)
        self.step("Check that the user received the new message")
        messages = gmail_api.wait_for_messages_to(recipient=username, messages_number=2)
        self.assertEqual(len(messages), 2)
        code = gmail_api.extract_code_from_message(messages[1]["content"])
        self.step("Register user with the received code")
        user, organization = User.api_register_after_onboarding(code, username)
        self.assert_user_in_org_and_roles(user, organization.guid, User.ORG_ROLES["manager"])

    def test_cannot_resend_not_existing_pending_invitation(self):
        username = "not_existing_user"
        self.assertRaisesUnexpectedResponse(404, "No pending invitation for {}".format(username),
                                            User.api_resend_user_invitation, username)

    @unittest.expectedFailure
    def test_cannot_resend_invitation_providing_empty_name(self):
        """DPNG-4657 http 500 when trying to use unsupported api endpoints"""
        self.assertRaisesUnexpectedResponse(404, "Not found", User.api_resend_user_invitation, "")

    def test_delete_pending_invitation(self):
        self.step("Invite new user")
        username = User.api_invite()
        self.assertInListWithRetry(username, User.api_get_pending_invitations)
        self.step("Delete pending user invitation")
        User.api_delete_user_invitation(username)
        self.assertNotInListWithRetry(username, User.api_get_pending_invitations)
        self.step("Get registration code from received message")
        code = gmail_api.get_invitation_code_for_user(username)
        self.step("Check that the user cannot register after deletion of pending invitation")
        self.assertRaisesUnexpectedResponse(403, "", User.api_register_after_onboarding, code, username)

    @unittest.expectedFailure
    def test_cannot_delete_not_existing_pending_invitation(self):
        """DPNG-4654 Typo in 'DELETE /rest/invitations/ error message."""
        self.step("Try to delete not existing invitation")
        username = "not_existing_user"
        self.assertRaisesUnexpectedResponse(404, "No pending invitation for {}".format(username),
                                            User.api_delete_user_invitation, username)

    @unittest.expectedFailure
    def test_cannot_delete_pending_invitation_providing_empty_name(self):
        """DPNG-4657 http 500 when trying to use unsupported api endpoints"""
        self.assertRaisesUnexpectedResponse(404, "Not found", User.api_delete_user_invitation, "")

    def test_cannot_get_pending_invitations_as_non_admin_user(self):
        self.step("Create new org and user")
        test_org = Organization.api_create()
        test_user = User.api_create_by_adding_to_organization(test_org.guid)
        test_user_client = test_user.login()
        self.step("As non admin user try to get pending invitations list")
        self.assertRaisesUnexpectedResponse(403, "Access is denied", User.api_get_pending_invitations, test_user_client)

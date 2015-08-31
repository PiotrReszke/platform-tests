import datetime
import time

from test_utils import config, gmail_api, get_logger, ApiTestCase
from objects import User, Organization


logger = get_logger("test onboarding")


class Onboarding(ApiTestCase):
    EXPECTED_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
    CLIENT_ID = "intel.data.tests@gmail.com"

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

    def test_simple_onboarding(self):
        username = User.get_default_username()
        org_name = "test_org_{}".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        User.api_invite(username)
        time.sleep(30)  # sleeping instead of timeout, to catch also when > 1 message is sent
        messages = gmail_api.get_messages(recipient=username)
        self.assertEqual(len(messages), 1,
                         "There are {} messages for {}. Expected: 1".format(len(messages), username))
        self._assert_message_correct(messages[0]["subject"], messages[0]["content"])

        code = gmail_api.extract_code_from_message(messages[0]["content"])
        user, organization = User.api_register_after_onboarding(code, username, org_name)
        organizations = Organization.api_get_list()
        self.assertInList(organization, organizations, "New organization was not found")
        users = User.api_get_list_via_organization(org_guid=organization.guid)
        self.assertInList(user, users, "Invited user was not found in new organization")


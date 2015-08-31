import datetime
import time

from test_utils import config, gmail_api
from test_utils.api_test_case import get_logger, ApiTestCase
from test_utils.objects import User, Organization


logger = get_logger("test onboarding")


class TestOnboarding(ApiTestCase):

    EXPECTED_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
    CLIENT_ID = "intel.data.tests@gmail.com"

    def _assert_message_correct(self, message_subject, message_content):
        expected_link = "https://console.{}/new-account".format(config.TEST_SETTINGS["TEST_ENVIRONMENT"])
        message_link = gmail_api.get_link_from_message(message_content)
        correct_link = (expected_link in message_link,
                        "Link to create account leads to another environment: {}, expected: {}".format(message_link,
                                                                                                       expected_link))
        correct_inviting_user = (config.TEST_SETTINGS["TEST_USERNAME"] in message_content,
                                 "Inviting user {} was not found in message content.".format(config.TEST_SETTINGS["TEST_USERNAME"]))
        correct_subject = (self.EXPECTED_EMAIL_SUBJECT in message_subject,
                           "Message subject {}. Expected: {}".format(message_subject, self.EXPECTED_EMAIL_SUBJECT))
        error_message = [error_msg for condition, error_msg in [correct_link, correct_inviting_user, correct_subject]
                         if not condition]
        self.assertTrue(correct_link[0] and correct_inviting_user[0] and correct_subject[0], error_message)

    def test_simple_onboarding(self):
        username = User.get_default_username()
        org_name = "test_org_{}".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        User.api_invite(username)
        time.sleep(30)

        message_query = gmail_api.get_query(username)
        message_ids = gmail_api.list_messages_matching_query(self.CLIENT_ID, message_query)
        self.assertEqual(len(message_ids), 1,
                         "There are {} messages for {}. Expected: 1".format(len(message_ids), username))
        message = gmail_api.get_message(message_ids[0].get("id"))
        self._assert_message_correct(*message)

        code = gmail_api.extract_code_from_message(message[1])
        user, organization, client = User.api_register_and_login(code, username, org_name)
        organizations = Organization.api_get_list()
        self.assertInList(organization, organizations, "New organization was not found")
        users = User.api_get_list_via_organization(organization_guid=organization.guid)
        self.assertInList(user, users, "Invited user was not found in new organization")


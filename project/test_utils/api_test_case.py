import functools
import unittest

from test_utils.api_client import UnexpectedResponseError
from test_utils.user_management.organization import Organization


class ApiTestCase(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        Organization.delete_test_orgs()

    def assertInList(self, member, container, msg=None):
        """Modeled after TestCase.assertIn(), but testing for equality, not identity."""
        for item in container:
            if member == item:
                return
        standardMsg = "{} not found in list".format(member, container)
        self.fail(self._formatMessage(msg, standardMsg))

    def assertNotInList(self, member, container, msg=None):
        """Reverse to assertInList"""
        for item in container:
            if member == item:
                standardMsg = "{} found in list".format(member, container)
                self.fail(self._formatMessage(msg, standardMsg))

    def assertRaisesUnexpectedResponse(self, status, error_message, callableObj, *args, **kwargs):
        with self.assertRaises(UnexpectedResponseError) as e:
            callableObj(*args, **kwargs)
        self.assertEqual([e.exception.status, e.exception.error_message],
                         [status, error_message],
                         "Error is {0} \"{1}\", expected {2} \"{3}\"".format(e.exception.status,
                                                                              e.exception.error_message,
                                                                              status, error_message))


def cleanup_after_failed_setup(cleanup_method):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:
                cleanup_method()
                raise
        return wrapped
    return wrapper
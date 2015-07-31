import functools
import unittest

import test_utils.objects.organization as org
from test_utils import get_logger, UnexpectedResponseError


logger = get_logger("api_test_case")


__all__ = ["ApiTestCase", "cleanup_after_failed_setup"]


class ApiTestCase(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        org.Organization.delete_test_orgs()

    def run(self, result=None):
        logger.info('\n******************************************************************\n'
                    '*\n'
                    '*\t\t %s\n'
                    '*\n'
                    '******************************************************************\n', self._testMethodName)
        return super().run(result=result)

    def assertInList(self, member, container, msg=None):
        """Modeled after TestCase.assertIn(), but testing for equality, not identity."""
        for item in container:
            if member == item:
                return
        standard_msg = "{} not found in list".format(member, container)
        self.fail(self._formatMessage(msg, standard_msg))

    def assertNotInList(self, member, container, msg=None):
        """Reverse to assertInList"""
        for item in container:
            if member == item:
                standard_msg = "{} found in list".format(member, container)
                self.fail(self._formatMessage(msg, standard_msg))

    def assertUnorderedListEqual(self, list1, list2):
        self.assertListEqual(sorted(list1), sorted(list2))

    def assertRaisesUnexpectedResponse(self, status, error_message, callableObj, *args, **kwargs):
        """If error message does not need to be checked, pass None"""
        with self.assertRaises(UnexpectedResponseError) as e:
            callableObj(*args, **kwargs)
        if error_message is not None:
            error = [e.exception.status, e.exception.error_message]
            expected = [status, error_message]
            self.assertEqual(error, expected, "Error is {0} \"{1}\", expected {2} \"{3}\"".format(*(error+expected)))
        else:
            self.assertEqual(e.exception.status, status,
                             "Error status is {0}, expected {1}".format(e.exception.status, status))

    def assertAttributesEqual(self, obj, expected_obj):
        if getattr(obj, "COMPARABLE_ATTRIBUTES", None) is None:
            raise ValueError("Object of type {} does not have attribute COMPARABLE_ATTRIBUTES".format(type(obj)))
        if type(obj) != type(expected_obj):
            raise TypeError("Cannot compare object of type {} with object of type {}".format(type(obj), type(expected_obj)))
        differences = []
        for attribute in obj.COMPARABLE_ATTRIBUTES:
            obj_val = getattr(obj, attribute)
            expected_val = getattr(expected_obj, attribute)
            if obj_val != expected_val:
                differences.append("{0}.{1}={2} not equal to {0}.{1}={3}".format(type(obj), attribute, obj_val, expected_val))
        if differences != []:
            self.fail("Objects are not equal:\n{}".format("\n".join(differences)))


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

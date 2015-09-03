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

from datetime import datetime
import functools
import time
import unittest

from objects import organization as org
from . import get_logger, UnexpectedResponseError

logger = get_logger("api_test_case")


__all__ = ["ApiTestCase", "cleanup_after_failed_setup"]


class ApiTestCase(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        org.Organization.cf_api_tear_down_test_orgs()

    def run(self, result=None):
        logger.info('\n******************************************************************\n'
                    '*\n'
                    '*\t\t %s\n'
                    '*\n'
                    '******************************************************************\n', self._testMethodName)
        return super().run(result=result)

    def get_timestamp(self):
        return datetime.now().strftime("%Y%m%d-%H%M%S%f")

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

    def assertEqualWithinTimeout(self, timeout, expected_result, callableObj, *args, **kwargs):
        now = time.time()
        while time.time() - now < timeout:
            result = callableObj(*args, **kwargs)
            if result == expected_result:
                return
            time.sleep(5)
        self.fail("{} and {} are not equal - within {}s".format(result, expected_result, timeout))

    def assertLenEqualWithinTimeout(self, timeout, expected_len, callableObj, *args, **kwargs):
        now = time.time()
        while time.time() - now < timeout:
            result = callableObj(*args, **kwargs)
            if len(result) == expected_len:
                return
            time.sleep(5)
        self.fail("{} != {} are not equal - within {}s".format(len(result), expected_len, timeout))


    def exec_within_timeout(self, timeout, callable_obj, *args, **kwargs):
        """Execute a callable until it does not raise an exception or until timeout"""
        now = time.time()
        exception = None
        while time.time() - now < timeout:
            try:
                return callable_obj(*args, **kwargs)
            except Exception as e:
                exception = e
                logger.warning("Exception {}".format(e))
                time.sleep(5)
        raise exception


def cleanup_after_failed_setup(*cleanup_methods):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:
                for cleanup_method in cleanup_methods:
                    cleanup_method()
                raise
        return wrapped
    return wrapper



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

from objects import organization as org, user as usr
from . import get_logger, UnexpectedResponseError


logger = get_logger("api_test_case")


__all__ = ["ApiTestCase", "cleanup_after_failed_setup"]

FUNCTIONS_TO_LOG = ('setUp', 'tearDown', 'setUpClass', 'tearDownClass')
SEPARATOR = "****************************** {} {} {} ******************************"


def log_fixture_separator(func):
    func_is_classmethod = type(func) is classmethod
    if func_is_classmethod:
        func = func.__func__
    func_name = func.__name__

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        class_name = "in {}".format(args[0].__name__) if func_is_classmethod else ""
        logger.info(SEPARATOR.format("BEGIN", func_name, class_name))
        func(*args, **kwargs)
        logger.info(SEPARATOR.format("END", func_name, class_name))

    if func_is_classmethod:
        return classmethod(wrapper)
    else:
        return wrapper


class SeparatorMeta(type):
    def __new__(mcs, name, bases, namespace):
        for attr, obj in namespace.items():
            if attr in FUNCTIONS_TO_LOG:
                namespace[attr] = log_fixture_separator(obj)
        return super(SeparatorMeta, mcs).__new__(mcs, name, bases, namespace)


class ApiTestCase(unittest.TestCase, metaclass=SeparatorMeta):

    STEP_NO = 0
    SUB_TEST_NO = 0

    @classmethod
    def tearDownClass(cls):
        org.Organization.cf_api_tear_down_test_orgs()
        usr.User.cf_api_tear_down_test_users()

    @classmethod
    def step(cls, message):
        """Log message as nth test step"""
        separator = "=" * 20
        step_logger = get_logger("STEP")
        step_logger.info("{0} Step {1} {2} {0}".format(separator, cls.STEP_NO, message))
        cls.STEP_NO += 1

    def subTest(self, msg=None, **params):
        separator = "*" * 20
        logged_params = ",".join(["{}={}".format(k, v) for k, v in params.items()])
        logger.info("{0} Sub test {1} ({2})".format(separator, self.SUB_TEST_NO, logged_params))
        sub_test_returns = super().subTest(msg, **params)
        self.__class__.STEP_NO = 0
        self.__class__.SUB_TEST_NO += 1
        return sub_test_returns

    def run(self, result=None):
        test_name = "{}.{}".format(self.__class__.__name__, self._testMethodName)
        separator = "*" * len(test_name)
        self.__class__.STEP_NO = self.__class__.SUB_TEST_NO = 0
        logger.info("\n{0}\n\n{1}\n\n{0}\n".format(separator, test_name))
        return super().run(result=result)

    @staticmethod
    def get_timestamp():
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

    def assertUnorderedListEqual(self, list1, list2, msg=None):
        self.assertListEqual(sorted(list1), sorted(list2), msg=msg)

    def assertRaisesUnexpectedResponse(self, status, error_message_phrase, callableObj, *args, **kwargs):
        """error_message_phrase - a phrase which should be a part of error message"""
        with self.assertRaises(UnexpectedResponseError) as e:
            callableObj(*args, **kwargs)
        status_correct = e.exception.status == status
        if error_message_phrase == "":
            error_message_contains_string = error_message_phrase == ""
        else:
            error_message_contains_string = error_message_phrase in e.exception.error_message
        self.assertTrue(status_correct and error_message_contains_string,
                        "Error is {0} \"{1}\", expected {2} \"{3}\"".format(e.exception.status,
                                                                            e.exception.error_message,
                                                                            status, error_message_phrase))

    def assertReturnsError(self, callableObj, *args, **kwargs):
        """Assert that response error code is 4XX or 5XX"""
        with self.assertRaises(UnexpectedResponseError) as e:
            callableObj(*args, **kwargs)
        status_first_digit = e.exception.status // 100
        self.assertIn(status_first_digit, (4, 5), "Status code: {}. Expected: 4XX or 5XX".format(e.exception.status))

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

    def assertEqualWithinTimeout(self, timeout, expected_result, callable_obj, *args, **kwargs):
        now = time.time()
        while time.time() - now < timeout:
            result = callable_obj(*args, **kwargs)
            if result == expected_result:
                return
            time.sleep(5)
        self.fail("{} and {} are not equal - within {}s".format(result, expected_result, timeout))

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



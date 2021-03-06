#
# Copyright (c) 2016 Intel Corporation
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

import pytest
from retry import retry

from modules.exceptions import UnexpectedResponseError
from modules.tap_object_model.flows import data_catalog


@retry(AssertionError, tries=20, delay=3)
def assert_equal_with_retry(expected_value, callableObj, *args, **kwargs):
    value = callableObj(*args, **kwargs)
    assert value == expected_value


@retry(AssertionError, tries=20, delay=3)
def assert_not_in_with_retry(something, get_list_method, *args, **kwargs):
    """Use when deleting something takes longer"""
    obj_list = get_list_method(*args, **kwargs)
    assert something not in obj_list, "{} was found on the list".format(something)


@retry(AssertionError, tries=30, delay=2)
def assert_in_with_retry(something, get_list_method, *args, **kwargs):
    """Use when adding something takes longer"""
    obj_list = get_list_method(*args, **kwargs)
    assert something in obj_list, "{} was not found on the list".format(something)


def assert_raises_http_exception(status, error_message_phrase, callableObj, *args, **kwargs):
    with pytest.raises(UnexpectedResponseError) as e:
        callableObj(*args, **kwargs)
    status_correct = e.value.status == status
    if error_message_phrase == "":
        error_message_contains_string = error_message_phrase == ""
    else:
        error_message_contains_string = error_message_phrase in e.value.error_message
    assert status_correct and error_message_contains_string, \
        "Error is {0} \"{1}\", expected {2} \"{3}\"".format(e.value.status, e.value.error_message,
                                                            status, error_message_phrase)

@retry(AssertionError, tries=2, delay=360)
def assert_greater_with_retry(get_list_method, list_to_compare, *args, **kwargs):
    obj_list = get_list_method(*args, **kwargs)
    assert len(obj_list) > len(list_to_compare)

def assert_returns_http_error(callable_obj, *args, **kwargs):
    with pytest.raises(UnexpectedResponseError) as e:
        callable_obj(*args, **kwargs)
    status_first_digit = e.exception.status // 100
    assert status_first_digit in (4, 5), "Status code: {}. Expected: 4XX or 5XX".format(e.exception.status)


def assert_no_errors(errors: list):
    assert len(errors) == 0, "\n".join([str(e) for e in errors])


def assert_unordered_list_equal(list1, list2, msg="Lists are not equal"):
    assert sorted(list1) == sorted(list2), msg


@retry(AssertionError, tries=2, delay=360)
def assert_dataset_greater_with_retry(value_to_compare, *args, **kwargs):
    _, dataset = data_catalog.create_dataset_from_link(*args, **kwargs)
    assert dataset.size > value_to_compare


def assert_datasets_not_empty(dataset_list):
    for dataset in dataset_list:
        assert dataset.size > 0

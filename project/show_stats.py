#!/usr/bin/env python
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

import unittest
import os
import argparse
from collections import Counter

from constants.priority_levels import Priority
from constants.tap_components import TapComponent
from run_tests import flatten_test_suite


ROOT_DIR = os.path.abspath("tests")
TEST_PATHS = [os.path.abspath(os.path.join(ROOT_DIR, directory)) for directory in os.listdir(ROOT_DIR)
              if os.path.isdir(os.path.join(ROOT_DIR, directory)) and directory.startswith("test_")]


def count_test_cases(test_suite):
    result = Counter({k: 0 for k in Priority.names() + TapComponent.names()})
    tests = flatten_test_suite(test_suite)
    for test in tests:
        if hasattr(test, 'priority'):
            result[test.priority.name] += 1
        if hasattr(test, 'components'):
            for component in test.components:
                result[component.name] += 1
    result["test_count"] = tests.countTestCases()
    return result


def parse_args():
    parser = argparse.ArgumentParser(description="Tests statistics")
    parser.add_argument("-p", "--show-priorities", help="show statistics according to priorities", action="store_true")
    parser.add_argument("-c", "--show-components", help="show statistics according to components", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    for directory in TEST_PATHS:
        loader = unittest.TestLoader()
        loaded_tests = loader.discover(directory)
        results = count_test_cases(loaded_tests)
        test_count = results["test_count"]
        print("Number of implemented tests in {}: {}".format(directory, test_count))
        if args.show_priorities:
            print("\tPriorities:")
            for k in Priority.names():
                print("\t\tPriority {}: {}".format(k, results[k]))
        if args.show_components:
            print("\tComponents:")
            for k in TapComponent.names():
                print("\t\tPriority {}: {}".format(k, results[k]))

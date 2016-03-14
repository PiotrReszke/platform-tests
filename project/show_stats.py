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

import os
import argparse
from collections import Counter

from constants.priority_levels import Priority
from constants.tap_components import TapComponent
from runner.loader import TapTestLoader


ROOT_DIR = os.path.abspath("tests")
TEST_PATHS = [os.path.abspath(os.path.join(ROOT_DIR, directory)) for directory in os.listdir(ROOT_DIR)
              if os.path.isdir(os.path.join(ROOT_DIR, directory)) and directory.startswith("test_")]


def parse_args():
    parser = argparse.ArgumentParser(description="Tests statistics")
    parser.add_argument("-p", "--show-priorities",
                        help="show statistics according to priorities",
                        action="store_true")
    parser.add_argument("-c", "--show-components",
                        help="show statistics according to components",
                        action="store_true")
    return parser.parse_args()


def count_by_priority(loader: TapTestLoader):
    priority_stats = {key: 0 for key in Priority.names()}
    for test in loader.tests:
        priority = getattr(test, "priority", None)
        if priority is not None:
            priority_stats[priority.name] += 1
    return priority_stats


def count_by_component(loader: TapTestLoader):
    component_stats = {key: 0 for key in TapComponent.names()}
    for test in loader.tests:
        components = getattr(test, "components", None)
        if components is not None:
            for component in components:
                component_stats[component.name] += 1
    return component_stats


def print_stats(stats: dict, stat_name: str):
    print("\t{}".format(stat_name))
    for name, count in stats.items():
        if count > 0:
            print("\t\t{}: {}".format(name, count))


if __name__ == "__main__":
    args = parse_args()
    for directory in TEST_PATHS:
        loader = TapTestLoader(path=directory)
        print("Tests in {}: {}".format(os.path.split(directory)[-1], len(loader.tests)))
        if args.show_priorities:
            print_stats(count_by_priority(loader), "Priority")
        if args.show_priorities:
            print_stats(count_by_component(loader), "Components")

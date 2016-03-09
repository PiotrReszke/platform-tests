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
import re
import time

from .db_client import DBClient
from .platform_version import VersionedComponent
from runner.tap_test_case import TapTestCase
from constants.test_results import TestResult


class TestResultDocument(object):
    COLLECTION_NAME = "test_result"

    def __init__(self, db_client: DBClient, run_id: str, suite: str, test_obj: TapTestCase, test_order: int,
                 platform_components: list):
        self.__db_client = db_client
        self.__run_id = run_id
        self.__suite = suite
        self.__name = self.__get_test_name(test_obj)
        self.__description = test_obj.shortDescription()
        self.__order = test_order
        self.__priority = test_obj.priority.name
        self.__components = self.__get_versioned_components(test_obj, platform_components)
        self.__main_component_name = self.__get_main_component_name(test_obj)

        self.__tags = getattr(test_obj, "tags", [])
        self.__defects = getattr(test_obj, "defects", [])

        self.__id = None
        self.__start_time = None
        self.__duration_s = None
        self.__result = None
        self.__reason_skipped = None
        self.__stacktrace = None
        self.log = None

    def start(self):
        self.__start_time = time.time()

    def end(self, result: TestResult, error=None, reason_skipped=None):
        self.__duration_s = round(time.time() - self.__start_time, ndigits=3)
        self.__result = result
        self.__stacktrace = error
        self.__reason_skipped = reason_skipped
        self.__insert()

    @staticmethod
    def __get_test_name(test_obj: TapTestCase):
        test_name, test_class, _ = re.split("\(|\)", str(test_obj))
        return "{}.{}".format(test_class, test_name)

    @staticmethod
    def __get_main_component_name(test_obj):
        if len(test_obj.components) > 0:
            return test_obj.components[0].name

    @staticmethod
    def __get_versioned_components(test_obj, platform_components):
        def is_test_component(platform_component):
            return platform_component.component in test_obj.components
        return list(filter(is_test_component, platform_components))

    def __to_mongo_document(self):
        return {
            "run_id": self.__run_id,
            "suite": self.__suite,
            "name": self.__name,
            "duration": self.__duration_s,
            "order": self.__order,
            "priority": self.__priority,
            "main_component": self.__main_component_name,
            "components": VersionedComponent.list_to_db_format(self.__components),
            "description": self.__description,
            "defects": self.__defects,
            "tags": self.__tags,
            "status": self.__result.value,
            "reason_skipped": self.__reason_skipped,
            "stacktrace": self.__stacktrace,
            "log": self.log
        }

    def __insert(self):
        self.__id = self.__db_client.insert(
            collection_name=self.COLLECTION_NAME,
            document=self.__to_mongo_document()
        )


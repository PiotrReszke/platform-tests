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

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestResult, TeamcityTestRunner

from .db_client import DBClient
from .test_run_document import TestRunDocument
from .test_result_document import TestResultDocument
from constants.test_results import TestResult
from test_utils import CONFIG


# select base class depending on whether tests are run on a TC agent or not
BaseResultClass = TeamcityTestResult if is_running_under_teamcity() else unittest.TextTestResult
BaseRunnerClass = TeamcityTestRunner if is_running_under_teamcity() else unittest.TextTestRunner


class DBTestResult(BaseResultClass):

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.__run = None
        self.__current_test = None
        self.db_client = DBClient(uri=CONFIG["database_url"])
        self.test_suite = CONFIG.get("test_suite")

    def startTestRun(self):
        super().startTestRun()
        self.__run = TestRunDocument(self.db_client, environment=CONFIG["domain"], environment_version=None,
                                     suite=self.test_suite, release=None, platform_components=[])
        self.__run.start()

    def stopTestRun(self):
        super().stopTestRun()
        self.__run.end()

    def startTest(self, test):
        super().startTest(test)
        self.__current_test = TestResultDocument(self.db_client, run_id=self.__run.id, suite=self.test_suite,
                                                 test_obj=test, test_order=self.testsRun, platform_components=[])
        self.__current_test.start()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.__current_test.end(result=TestResult.success)
        self.__run.update_result(result=TestResult.success)

    def addError(self, test, err):
        super().addError(test, err)
        self.__current_test.end(result=TestResult.error, error=self._exc_info_to_string(err, test))
        self.__run.update_result(result=TestResult.error)

    def addFailure(self, test, err):
        super().addError(test, err)
        self.__current_test.end(result=TestResult.failure, error=self._exc_info_to_string(err, test))
        self.__run.update_result(result=TestResult.failure)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.__current_test.end(result=TestResult.skip, reason_skipped=reason)
        self.__run.update_result(result=TestResult.skip)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.__current_test.end(result=TestResult.expected_failure, error=self._exc_info_to_string(err, test))
        self.__run.update_result(result=TestResult.expected_failure)

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.__current_test.end(result=TestResult.unexpected_success)
        self.__run.update_result(result=TestResult.unexpected_success)

    def run(self, test):
        return super().run(test)



class DBTestRunner(BaseRunnerClass):
    resultclass = DBTestResult

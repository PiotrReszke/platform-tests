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

from configuration import config
from modules.mongo_reporter.reporter import MongoReporter


@pytest.fixture(scope="session", autouse=True)
def log_test_run_in_database(request):
    if config.CONFIG["database_url"] is not None:
        mongo_reporter = MongoReporter(mongo_uri=config.CONFIG["database_url"], run_id=config.CONFIG["test_run_id"])
        mongo_reporter.on_run_start(environment=config.CONFIG["domain"],
                                    environment_version=None,
                                    platform_components=[],
                                    tests_to_run_count=len(request.session.items))

        def finalizer():
            mongo_reporter.on_run_end()
        request.addfinalizer(finalizer)
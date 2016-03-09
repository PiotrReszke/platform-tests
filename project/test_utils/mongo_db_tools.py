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

from pymongo import MongoClient

from test_utils import get_logger


logger = get_logger("MongoDbTools")

TEST_RUN = "test_run"
TEST_RESULT = "test_result"


class MongoDbTools:
    def __init__(self, host=os.environ.get("DATABASE_URL"), database_name="primer"):
        client = MongoClient(host=host)
        self.database = client[database_name]

    def _send_data(self, collection_name, data):
        logger.info("Add to collection '{}' new row {}".format(collection_name, data))
        result = self.database[collection_name].insert_one(data)
        return result

    def _replace_data(self, collection_name, data_filter, data):
        logger.info("Replace row {} in collection '{}' with {}".format(data_filter, collection_name, data))
        result = self.database[collection_name].replace_one(data_filter, data)
        return result

    def add_to_test_run(self, data):
        """Add data to test_run collection."""
        return self._send_data(TEST_RUN, data)

    def add_to_test_result(self, data):
        """Add data to test_result collection."""
        return self._send_data(TEST_RESULT, data)

    def replace_in_test_run(self, data_filter, data):
        """Replace data in test_run collection
            data_filter: replace row where chosen {key: value} exists
            data: new data
        """
        return self._replace_data(TEST_RUN, data_filter, data)

    def replace_in_test_result(self, data_filter, data):
        """Replace data in test_result collection
            data_filter: replace row where chosen {key: value} exists
            data: new data
        """
        return self._replace_data(TEST_RESULT, data_filter, data)

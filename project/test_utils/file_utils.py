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

import csv
from datetime import datetime
import os


__all__ = ["generate_csv_file", "tear_down_test_files"]


TMP_FILE_DIR = "/tmp/test_files"
TEST_FILES = []  # list of generated files - used for cleanup


def generate_csv_file(column_count=10, size=None, row_count=10):
    """
    Return path to the new file.
    Pass row_count or size (in bytes) - if both are passed, size takes precedence.
    """
    os.makedirs(TMP_FILE_DIR, exist_ok=True)
    file_path = os.path.join(TMP_FILE_DIR, "test_file_{}.csv".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f')))
    with open(file_path, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["COL_{}".format(i) for i in range(column_count)])
        row = ["0123456789" for _ in range(column_count)]
        if size is not None:
            while csv_file.tell() < size:
                csv_writer.writerow(row)
        else:
            for i in range(row_count):
                csv_writer.writerow(row)
    TEST_FILES.append(file_path)
    return file_path


def tear_down_test_files():
    while len(TEST_FILES) > 0:
        file_path = TEST_FILES.pop()
        os.remove(file_path)






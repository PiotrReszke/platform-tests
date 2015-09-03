##############################################################################
# INTEL CONFIDENTIAL
#
# Copyright 2015 Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code (Material) are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,
# copied, reproduced, modified, published, uploaded, posted, transmitted,
# distributed, or disclosed in any way without Intel's prior express written
# permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or
# delivery of the Materials, either expressly, by implication, inducement,
# estoppel or otherwise. Any license under such intellectual property rights
# must be express and approved by Intel in writing.
##############################################################################

import os
import re

import trustedanalytics as ta

from common import AtkTestException, parse_arguments, check_uaa_file, remove_test_tables_from_database

TEST_TAB_PATTERN = "test_org_[0-9]{8}_[0-9]{6}_[0-9]{6}$"
TEST_DEFAULT_PATTERN = "test_tab_[0-9]{8}_[0-9]{6}_[0-9]{6}$"

parameters = parse_arguments()

directory = os.path.dirname(__file__)

uaa_file_name = os.path.join(directory, parameters.uaa_file_name)
ta.create_credentials_file(uaa_file_name)

check_uaa_file(uaa_file_name)

print("uaa file found")

query = "SHOW DATABASES"  # don't put semicolon at the end
print("\nQuery: {}".format(query))
hq = ta.HiveQuery(query)
frame = ta.Frame(hq)

frame_content = frame.inspect(n=50)  # returns 50 rows
frame_rows = frame_content.rows
databases_to_remove = [row for row in frame_rows if re.match(TEST_TAB_PATTERN, row[0])]
print(databases_to_remove)

for database in databases_to_remove:
    remove_test_tables_from_database(database, TEST_DEFAULT_PATTERN)

remove_test_tables_from_database(["default"], TEST_DEFAULT_PATTERN)





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

import argparse
import os
import re

import trustedanalytics as ta


class AtkTestException(AssertionError):
    pass


def parse_arguments():
    parser = argparse.ArgumentParser(description="ATK Python Client Test")
    parser.add_argument("--organization",
                        help="organization where transfer was uploaded")
    parser.add_argument("--transfer",
                        help="transfer name of submitted document")
    parser.add_argument("--uaa_file_name",
                        help="uaa file name that will be created by script")
    parser.add_argument("--target_uri",
                        help="hdfs storage address")
    return parser.parse_args()

def check_uaa_file(uaa_file_name):
    if not os.path.isfile(uaa_file_name):
        raise AtkTestException("authorization file not found")
    if os.stat(uaa_file_name).st_size == 0:
        raise AtkTestException("authorization file is empty")
    print("UAA file correctly created")

def remove_test_tables_from_database(database, test_table_pattern):
    query_show_tables = "SHOW TABLES IN " + database[0]
    print("\nQuery: {}".format(query_show_tables))
    hq_show_tables = ta.HiveQuery(query_show_tables)
    frame_show_tables = ta.Frame(hq_show_tables)
    frame_show_tables_content = frame_show_tables.inspect(n=50)
    tables_to_remove = frame_show_tables_content.rows
    if database[0] == "default":
        tables_to_remove = [row for row in tables_to_remove if re.match(test_table_pattern, row[0])]
    print("tables to remove: ", tables_to_remove)
    for tab in tables_to_remove:
        delete_tab_query = "DROP TABLE " + database[0] + "." + tab[0]
        print("Query: {}".format(delete_tab_query))
        hq_tab_delete = ta.HiveQuery(delete_tab_query)
        ta.Frame(hq_tab_delete)
    if database[0] != "default":
        delete_db_query = "DROP DATABASE " + database[0]
        print("Query: {}".format(delete_db_query))
        hq_db_delete = ta.HiveQuery(delete_db_query)
        ta.Frame(hq_db_delete)

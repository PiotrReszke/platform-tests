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
import datetime

import trustedanalytics as ta

from common import AtkTestException, parse_arguments, check_uaa_file

parameters = parse_arguments()

ta.create_credentials_file(parameters.uaa_file_name)

check_uaa_file(parameters.uaa_file_name)

query_source = "select * from " + parameters.organization + "." + parameters.transfer
print("Query: {}".format(query_source))
hq = ta.HiveQuery(query_source)
original_frame = ta.Frame(hq)

destination_table = "test_tab_{}".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))

print("exporting...")
original_frame.export_to_hive(destination_table)

query_destination = "select * from default." + destination_table
print("Query: {}".format(query_destination))
hq_default = ta.HiveQuery(query_destination)
exported_frame = ta.Frame(hq_default)

original_table_rows = original_frame.row_count
exported_table_rows = exported_frame.row_count

print("original_table_rows: ", original_table_rows)
print("exported_table_rows: ", exported_table_rows)

original_table_content = original_frame.inspect()
exported_table_content = exported_frame.inspect()

print("original_table_content: ", original_table_content)
print("exported_table_content: ", exported_table_content)

original_table_inspect_list = original_table_content.rows
exported_table_inspect_list = exported_table_content.rows

if original_table_rows == exported_table_rows and original_table_inspect_list == exported_table_inspect_list:
    print("Table {} exported correctly".format(parameters.organization + "." + parameters.transfer))
else:
    raise AtkTestException("Exported data is not same to original one")


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

import trustedanalytics as ta

from common import AtkTestException, parse_arguments, check_uaa_file

parameters = parse_arguments()

ta.create_credentials_file(parameters.uaa_file_name)

check_uaa_file(parameters.uaa_file_name)

query_select = "SELECT * FROM " + parameters.organization + "." + parameters.transfer
print("Query: {}".format(query_select))
hq = ta.HiveQuery(query_select)
frame_select = ta.Frame(hq)

column_names_list = frame_select.column_names
column_names_len = len(column_names_list)

print("\n------------ Test: group_by method ------------")
frame_group = frame_select.group_by(column_names_list[0], ta.agg.count)
frame_group_content = frame_group.inspect()
print("frame_group_content: ", frame_group_content)

frame_group_columns_list = frame_group.column_names
frame_group_columns_len = len(frame_group_columns_list)

if frame_group_columns_len == 2 and frame_group_columns_list[0] == column_names_list[0] and \
                frame_group_columns_list[1] == 'count':
    print("Table {} grouped correctly".format(parameters.organization + "." + parameters.transfer))
else:
    raise AtkTestException("Table {} was NOT grouped correctly".format(parameters.organization + "." +
                                                                       parameters.transfer))

print("\n------------ Test: add_column method ------------")
frame_select.add_columns(lambda row: "", ("test_column", str))

frame_add_columns_list = frame_select.column_names
frame_add_columns_len = len(frame_add_columns_list)

if frame_add_columns_len == (column_names_len+1) and frame_add_columns_list[column_names_len] == "test_column":
    print("Column was added to table {}".format(parameters.organization + "." + parameters.transfer))
else:
    raise AtkTestException("Column was NOT added to table {}".format(parameters.organization + "." +
                                                                       parameters.transfer))

print("\n------------ Test: drop_column method ------------")
frame_select.drop_columns('test_column')

frame_drop_columns_list = frame_select.column_names
frame_drop_columns_len = len(frame_drop_columns_list)

if frame_drop_columns_len == column_names_len and 'test_column' not in frame_drop_columns_list:
    print("Column 'test_column' was dropped in table {}".format(parameters.organization + "." + parameters.transfer))
else:
    raise AtkTestException("Column was NOT dropped in table {}".format(parameters.organization + "." +
                                                                       parameters.transfer))

print("\n------------ Test: drop_frames method ----------------")
ta.drop_frames([frame_select, frame_group])
if frame_select.status != 'Active' and frame_group.status != 'Active':
    print("Frames {}, {} removed successfully".format(frame_select, frame_group))
else:
    raise AtkTestException("Frames {}, {} NOT deleted. Status of both frames should be Deleted ".format(frame_select,
                                                                                                        frame_group))

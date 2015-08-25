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

#!/usr/bin/python2.7
import argparse
import os

import taprootanalytics as ta

class AtkTestException(AssertionError):
    pass

def parse_arguments():
    parser = argparse.ArgumentParser(description="ATK Python Client Test")
    parser.add_argument("--organization",
                        help="organization where transfer was uploaded")
    parser.add_argument("--atk",
                        help="ATK instance server URI for client")
    parser.add_argument("--transfer",
                        help="transfer name of submitted document")
    parser.add_argument("--uaa_file_name",
                        help="uaa file name that will be created by script")
    return parser.parse_args()

print("starting")
parameters = parse_arguments()

dir = os.path.dirname(__file__)

uaa_file_name = os.path.join(dir, parameters.uaa_file_name)
ta.create_credentials_file(uaa_file_name)

if not os.path.isfile(uaa_file_name):
    raise AtkTestException("authorization file not found")
if os.stat(uaa_file_name).st_size == 0:
    raise AtkTestException("authorization file is empty")

print("uaa file found")

ta.server.uri = parameters.atk
print("server set")

ta.connect(uaa_file_name)

print("connected")

query = "select * from " + parameters.organization + "." + parameters.transfer

print("Query: {}".format(query))

hq = ta.HiveQuery(query)

frame = ta.Frame(hq)
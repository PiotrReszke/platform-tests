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

import logging
import sys


__all__ = ["get_logger", "log_command"]


format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
logging.basicConfig(stream=sys.stdout, format=format, level=logging.DEBUG)
logging.getLogger("pyswagger.core").setLevel(logging.WARNING)
logging.getLogger("pyswagger.getter").setLevel(logging.WARNING)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)



def get_logger(name):
    return logging.getLogger(name)


def log_command(command, replace=None):
    logger = get_logger("shell command")
    msg = "Execute {}".format(" ".join(command))
    if replace is not None:
        msg = msg.replace(*replace)
    logger.info(msg)

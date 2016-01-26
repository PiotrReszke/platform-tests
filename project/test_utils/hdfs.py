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

import os
import re

from . import get_logger, config, SshClient, HdfsException




__all__ = ["Hdfs"]


logger = get_logger("hdfs")


class Hdfs(object):

    def __init__(self):
        hostname = "cdh-master-0"
        username = "ec2-user"
        path_to_key = os.path.expanduser(os.path.join("~", ".ssh", "auto-deploy-virginia.pem"))

        via_hostname = "cdh.{}".format(config.CONFIG["domain"])
        self.ssh_client = SshClient(hostname=hostname, username=username, path_to_key=path_to_key,
                                    via_hostname=via_hostname, via_username=username, via_path_to_key=path_to_key)
        logger.info("Accessing HDFS on {} via {}".format(hostname, via_hostname))
        self.hadoop_fs = ["hadoop", "fs"]

    def _execute(self, command):
        stdout, stderr = self.ssh_client.exec_command(command)
        if stderr != "":
            raise HdfsException(stderr)
        return stdout

    def ls(self, directory_path):
        """Execute ls on a directory in hdfs. Return a list of file paths."""
        command = self.hadoop_fs + ["-ls", directory_path]
        output = self._execute(command)
        paths = []
        for line in [line for line in output.split("\n")[1:-1]]:
            r = re.search("\/.*$", line)
            paths.append(line[r.start():r.end()])
        return paths

    def cat(self, file_path):
        command = self.hadoop_fs + ["-cat", file_path]
        output = self._execute(command)
        return output






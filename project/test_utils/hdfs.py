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

import re

import spur

from . import get_logger, log_command, config


__all__ = ["Hdfs"]


logger = get_logger("hdfs")


class Hdfs(object):

    def __init__(self, node_name, username="ec2-user"):
        test_environment = config.CONFIG["domain"]
        self.hostname = "cdh.{}".format(test_environment)
        self.username = username
        logger.info("Accessing HDFS on {}@{}".format(self.username, self.hostname))
        self.node_name = "hdfs://{}/".format(node_name)
        self.hadoop_fs = ["hadoop", "fs", "-fs", self.node_name]
        if test_environment == "gotapaas.eu":  # due to problems with hadoop config on cdh.gotapaas.eu
            self._switch_user("hdfs")

    def _execute(self, command):
        log_command(command)
        with spur.SshShell(hostname=self.hostname,
                           username=self.username,
                           password=config.CONFIG["ssh_key_passphrase"]) as shell:
            result = shell.run(command)
        if result.return_code != 0:
            raise result.to_error()
        return result

    def _switch_user(self, user):
        self._execute(["sudo", "su", "-", user])

    def ls(self, directory_path):
        """Execute ls on a directory in hdfs. Return a list of file paths."""
        command = self.hadoop_fs + ["-ls", directory_path]
        output = self._execute(command).output.decode()
        paths = []
        for line in [line for line in output.split("\n")[1:-1]]:
            r = re.search("\/.*$", line)
            paths.append(line[r.start():r.end()])
        return paths

    def cat(self, file_path):
        command = self.hadoop_fs + ["-cat", file_path]
        output = self._execute(command).output.decode()
        return output

    def test_file(self, filepath):
        command = self.hadoop_fs + ["-test", "-e", filepath]
        log_command(command)
        with spur.SshShell(hostname=self.hostname, username=self.username) as shell:
            return shell.run(command).return_code


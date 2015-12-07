#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License";
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

import paramiko

from test_utils import log_command


class SshClient(object):

    def __init__(self, hostname, username, path_to_key=None, port=22, via_hostname=None, via_username=None,
                 via_path_to_key=None, via_port=22):
        if via_hostname is None:
            # connect directly
            target_hostname = hostname
            target_port = port
            target_username = username
            target_key_path = path_to_key
            channel=None
        else:
            # connect with port forwarding
            target_hostname = "127.0.0.1"
            target_port = 1234
            target_username = via_username
            target_key_path = via_path_to_key
            self.proxy = paramiko.SSHClient()
            self.proxy.set_missing_host_key_policy(paramiko.client.WarningPolicy())
            self.proxy.connect(via_hostname, port=via_port, username=username, key_filename=path_to_key)
            proxy_transport = self.proxy.get_transport()
            channel = proxy_transport.open_channel("direct-tcpip", (hostname, port), (target_hostname, target_port))
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.client.WarningPolicy())
        self.client.connect(
            target_hostname,
            port=target_port,
            username=target_username,
            sock=channel,
            key_filename=target_key_path
        )

    def exec_command(self, command):
        log_command([command])
        _, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()




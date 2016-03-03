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

import os
import paramiko
import sshtunnel

from . import log_command, get_logger

__all__ = ["DirectSshClient", "NestedSshClient", "SshTunnel"]


logger = get_logger(__name__)

SSH_POLICY = paramiko.AutoAddPolicy()

class DirectSshClient(object):
    def __init__(self, hostname, username, port=22, path_to_key=None):
        self.hostname = hostname
        self.username = username
        self.port = port
        self.path_to_key = path_to_key
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(SSH_POLICY)

    def connect(self):
        self.client.connect(self.hostname, port=self.port, username=self.username, key_filename=self.path_to_key)

    def disconnect(self):
        self.client.close()

    def exec_command(self, command):
        log_command(command)
        command = " ".join(command)
        _, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()

class NestedSshClient(object):
    def __init__(self, hostname, username, path_to_key=None, port=22, via_hostname=None, via_username=None,
                 via_path_to_key=None, via_port=22, local_port=1234):
        self.hostname = hostname
        self.username = username
        self.port = port
        self.path_to_key = path_to_key
        self.via_hostname = via_hostname
        self.via_username = via_username
        self.via_path_to_key = via_path_to_key
        self.via_port = via_port
        self.local_port = local_port
        if self.via_username is None:
            self.via_username = self.username
        if self.via_path_to_key is None:
            self.via_path_to_key = self.path_to_key
        self.proxy = paramiko.SSHClient()
        self.proxy.set_missing_host_key_policy(SSH_POLICY)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(SSH_POLICY)

    def connect(self):
        self.proxy.connect(self.via_hostname, port=self.via_port, username=self.via_username,
                           key_filename=self.via_path_to_key)
        proxy_transport = self.proxy.get_transport()
        channel = proxy_transport.open_channel("direct-tcpip", dest_addr=(self.hostname, self.port),
                                               src_addr=("localhost", self.local_port))
        self.client.connect("localhost", port=self.local_port, username=self.username, sock=channel,
                            key_filename=self.path_to_key)

    def disconnect(self):
        self.proxy.close()
        self.client.close()

    def exec_command(self, command):
        log_command(command)
        command = " ".join(command)
        _, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()

class SshTunnel(object):
    def __init__(self, hostname, username, path_to_key=None, port=22, via_hostname=None, via_port=22, local_port=1234):
        self.hostname = hostname
        self.username = username
        self.port = port
        self.path_to_key = path_to_key
        self.via_hostname = via_hostname
        self.via_port = via_port
        self.local_port = local_port
        ssh_address = (self.via_hostname, self.via_port)
        ssh_private_key = os.path.expanduser(self.path_to_key)
        ssh_private_key = paramiko.RSAKey.from_private_key_file(ssh_private_key)
        local_bind_address = ("localhost", self.local_port)
        remote_bind_address = (self.hostname, self.port)
        self.client = sshtunnel.SSHTunnelForwarder(ssh_address=ssh_address, ssh_username=self.username,
                                                   ssh_private_key=ssh_private_key, local_bind_address=local_bind_address,
                                                   remote_bind_address=remote_bind_address)

    def connect(self):
        self.client.start()

    def disconnect(self):
        self.client.stop()

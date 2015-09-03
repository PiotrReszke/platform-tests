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
import subprocess
import pexpect
import time

from . import log_command, get_logger, config, platform_api_calls as api

__all__ = ["ATKtools"]


logger = get_logger("ATKtools")


class AtkScriptException(AssertionError):
    pass


class ATKtools(object):

    HOME = os.path.expanduser("~")

    def __init__(self, name, interpreter_version="python2"):
        self.path = os.path.join(self.HOME, "virtualenvs", name)
        self.system_interpreter = os.path.join("/usr/bin", interpreter_version)
        self.interpreter = os.path.join(self.path, "bin", interpreter_version)
        self.pip = os.path.join(self.path, "bin/pip")

    def create(self):
        command = ["virtualenv", "-p", self.system_interpreter, self.path]
        log_command(command)
        subprocess.check_call(command)

    def delete(self):
        command = ["rm", "-rf", self.path]
        log_command(command)
        subprocess.check_call(command)

    def pip_install(self, package_name, **pip_options):
        command = [self.pip, "install"]
        for option_name, value in pip_options.items():
            command += ["--" + option_name.replace("_", "-"), value]
        command += [package_name]
        log_command(command)
        subprocess.check_call(command)

    def pip_install_local_package(self, package_path):
        """Package path is path where the package's setup.py is located"""
        command = [self.pip, "install", "-e", package_path]
        log_command(command)
        subprocess.check_call(command)

    def pip_uninstall(self, package_name):
        command = [self.pip, "uninstall", package_name]
        log_command(command)
        yes = subprocess.Popen(["/usr/bin/yes"], stdout=subprocess.PIPE)
        subprocess.check_call(command, stdin=yes.stdout)

    def run_script(self, script_path, arguments=()):
        command = [self.interpreter, script_path]
        if len(arguments) != 0:
            for k, v in arguments.items():
                command += [k, v]
        log_command(command)
        return subprocess.check_call(command)

    def run_atk_script(self, script_path, atk_url, arguments=None):
        command = [self.interpreter, script_path]
        if arguments is not None:
            for k, v in arguments.items():
                command += [k, v]
        log_command(command)

        username = config.TEST_SETTINGS["TEST_USERNAME"]
        password = config.TEST_SETTINGS["TEST_PASSWORD"]

        child = pexpect.spawn(" ".join(command))
        child.expect("URI of ATK or OAuth server:")
        child.sendline(atk_url)
        child.expect("User name:")
        child.sendline(username)
        child.expect("Password:")
        child.sendline(password)
        time.sleep(30)
        child.sendline("y")
        child.expect(pexpect.EOF, timeout=120)
        response = child.before.decode("utf-8")

        logger.info("Atk script output:\n{}".format(response))

        if "Connected" not in response:
            raise AtkScriptException("Python client failed to connect to ATK instance")
        if "100.00% Tasks" not in response:
            raise AtkScriptException("Hive could not find resources")

        return response

    @classmethod
    def api_get_atk_client_file(cls, client=None):
        atk_file_name = api.api_get_atk_client_file_name(client)
        api.api_get_file(atk_file_name, atk_file_name, client)
        return atk_file_name


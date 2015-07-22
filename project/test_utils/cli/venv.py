import os
import subprocess

from test_utils.logger import log_command


__all__ = ["Virtualenv"]


class Virtualenv(object):

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
        for option_name, value in pip_options:
            command += ["--" + option_name, value]
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

    def run_script(self, script_path):
        command = [self.interpreter, script_path]
        log_command(command)
        return subprocess.check_call(command)
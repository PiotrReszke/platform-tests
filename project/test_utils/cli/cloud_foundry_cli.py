import subprocess

import test_utils.config as config
from test_utils.cli.shell_commands import log_command
from test_utils import get_logger

logger = get_logger("cloud_foundry_cli")


def cf_login(organization, space):
    api_url = config.get_config_value("cf_endpoint")
    username = config.TEST_SETTINGS["TEST_USERNAME"]
    password = config.TEST_SETTINGS["TEST_PASSWORD"]
    command = ["cf", "login", "-a", api_url, "-u", username, "-p", password, "-o", organization, "-s", space]
    log_command(command, replace=(password, "[SECRET]"))
    subprocess.check_call(command)


def cf_target(organization=None, space=None):
    command = ["cf", "target"]
    if organization is not None:
        command += ["-o", organization]
    if space is not None:
        command += ["-s", space]
    log_command(command)
    subprocess.check_call(command)


def cf_push(app_name=None):
    command = ["cf", "push"]
    if app_name is not None:
        command += [app_name]
    log_command(command)
    subprocess.check_call(command)


def cf_apps():
    command = ["cf", "apps"]
    log_command(command)
    return subprocess.check_output(["cf", "apps"]).decode()

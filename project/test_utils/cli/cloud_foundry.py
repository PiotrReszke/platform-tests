import subprocess

from test_utils.logger import get_logger, log_command
import test_utils.config as config


__all__ = ["cf_login", "cf_target", "cf_push", "cf_apps", "cf_curl", "cf_marketplace", "cf_services", "cf_cs", "cf_stop", "cf_start", "cf_delete", "cf_env"]


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


def cf_push(local_path, local_jar):
    command = ["cf", "push", "-f", local_path, "-p", local_jar]
    log_command(command)
    return subprocess.check_output(command).decode()

def cf_apps():
    command = ["cf", "apps"]
    log_command(command)
    return subprocess.check_output(command).decode()

def cf_curl(path, http_method):
    command = ["cf", "curl", path, "-X", http_method]
    return subprocess.check_output(command).decode()

def cf_marketplace():
    command = ["cf", "marketplace"]
    log_command(command)
    return subprocess.check_output(["cf", "marketplace"]).decode()

def cf_services(space_guid):
    command = ["cf", "curl", "v2/spaces/{0}/services".format(space_guid)]
    log_command(command)
    return subprocess.check_output(command).decode()

def cf_cs(service, instance, plans="shared"):
    command = ["cf", "cs", service, plans, instance]
    log_command(command)
    subprocess.check_call(command)

def cf_stop(app_name):
    command = ["cf", "stop", app_name]
    log_command(command)
    subprocess.check_call(command)

def cf_start(app_name):
    command = ["cf", "start", app_name]
    log_command(command)
    subprocess.check_call(command)

def cf_delete(app_name):
    command = ["cf", "delete", "-f", app_name]
    log_command(command)
    subprocess.check_call(command)

def cf_env(app_name):
    command = ["cf", "env", app_name]
    log_command(command)
    return subprocess.check_output(command).decode()

import functools
import subprocess

import test_utils.config as config
from test_utils import CfApiClient, get_logger, log_command


__all__ = ["cf_login", "cf_target", "cf_push", "cf_marketplace", "cf_cs", "cf_stop", "cf_start", "cf_delete",
           "cf_env", "cf_api_get_service_instances", "cf_api_app_summary", "cf_api_env", "cf_api_services",
           "cf_api_space_summary", "cf_api_org_auditors", "cf_api_org_managers", "cf_api_org_billing_managers"]


logger = get_logger("cloud_foundry_cli")


# ------------------------------- command line interface ------------------------------- #

def log_output_on_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.SubprocessError as e:
            logger.error(e.output)
            raise
    return wrapper


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


@log_output_on_error
def cf_push(local_path, local_jar):
    command = ["cf", "push", "-f", local_path, "-p", local_jar]
    log_command(command)
    return subprocess.check_output(command).decode()


@log_output_on_error
def cf_marketplace():
    command = ["cf", "marketplace"]
    log_command(command)
    return subprocess.check_output(["cf", "marketplace"]).decode()


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


@log_output_on_error
def cf_env(app_name):
    command = ["cf", "env", app_name]
    log_command(command)
    return subprocess.check_output(command).decode()


# ------------------------------- cf api ------------------------------- #

def __get_all_pages(path, query_params=None):
    """For requests which return paginated results"""
    query_params = query_params or {}
    resources = []
    page_num = 1
    while True:
        params = {"results-per-page": 100, "page": page_num}.update(query_params)
        response = CfApiClient.get_client().call(method="GET", path=path, params=params)
        resources.extend(response["resources"])
        if page_num == response["total_pages"]:
            break
        page_num += 1
    return resources


def cf_api_get_service_instances(org_guid):
    logger.info("------------------ CF: service instances for org {} ------------------".format(org_guid))
    return __get_all_pages(path="service_instances", query_params={"q": "organization_guid:{}".format(org_guid)})


def cf_api_env(app_guid):
    logger.info("------------------ CF: env for app {} ------------------".format(app_guid))
    return CfApiClient.get_client().call(method="GET", path="apps/{}/env".format(app_guid))


def cf_api_services(space_guid):
    logger.info("------------------ CF: services for space {} ------------------".format(space_guid))
    return CfApiClient.get_client().call(method="GET", path="spaces/{}/services".format(space_guid))


def cf_api_app_summary(app_guid):
    logger.info("------------------ CF: summary for app {} ------------------".format(app_guid))
    return CfApiClient.get_client().call("GET", "apps/{}/summary".format(app_guid))


def cf_api_space_summary(space_guid):
    """Equal to running cf apps"""
    logger.info("------------------ CF: summary for space {} ------------------".format(space_guid))
    return CfApiClient.get_client().call("GET", "spaces/{}/summary".format(space_guid))


def cf_api_org_managers(org_guid):
    logger.info("------------------ CF: managers in org {} ------------------".format(org_guid))
    return __get_all_pages(path="organizations/{}/managers".format(org_guid))


def cf_api_org_billing_managers(org_guid):
    logger.info("------------------ CF: billing managers in org {} ------------------".format(org_guid))
    return __get_all_pages(path="organizations/{}/billing_managers".format(org_guid))


def cf_api_org_auditors(org_guid):
    logger.info("------------------ CF: auditors in org {} ------------------".format(org_guid))
    return __get_all_pages(path="organizations/{}/auditors".format(org_guid))


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

import functools
import subprocess
import time

from test_utils import CfApiClient, get_logger, log_command, get_config_value, TEST_SETTINGS


__all__ = ["cf_login", "cf_target", "cf_push", "cf_marketplace", "cf_create_service", "cf_stop", "cf_start", "cf_delete",
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
    api_url = get_config_value("cf_endpoint")
    username = TEST_SETTINGS["TEST_USERNAME"]
    password = TEST_SETTINGS["TEST_PASSWORD"]
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
def cf_apps():
    command = ["cf", "apps"]
    log_command(command)
    return subprocess.check_output(command).decode()


@log_output_on_error
def cf_marketplace(service_name=None):
    command = ["cf", "marketplace"]
    if service_name is not None:
        command += ["-s", service_name]
    log_command(command)
    return subprocess.check_output(command).decode()


@log_output_on_error
def cf_create_service(broker_name, plan, instance_name):
    command = ["cf", "create-service", broker_name, plan, instance_name]
    log_command(command)
    return subprocess.check_output(command).decode()


def cf_services():
    command = ["cf", "services"]
    log_command(command)
    return subprocess.check_output(command).decode()


def cf_stop(app_name):
    command = ["cf", "stop", app_name]
    log_command(command)
    subprocess.check_call(command)


def cf_start(app_name):
    command = ["cf", "start", app_name]
    log_command(command)
    subprocess.check_call(command)


def cf_delete(app_name):
    command = ["cf", "delete", app_name, "-f"]
    log_command(command)
    subprocess.check_call(command)


@log_output_on_error
def cf_env(app_name):
    command = ["cf", "env", app_name]
    log_command(command)
    return subprocess.check_output(command).decode()


@log_output_on_error
def cf_delete_with_routes(app_name):
    command = ["cf", "delete", app_name, "-f", "-r"]
    log_command(command)
    return subprocess.check_output(command).decode()


def cf_delete_space(space_name):
    command = ["cf", "delete-space", space_name, "-f"]
    log_command(command)
    return subprocess.check_call(command)


def cf_unbind_service(app_name, service_name):
    command = ["cf", "unbind-service", app_name, service_name]
    log_command(command)
    return subprocess.check_call(command)


@log_output_on_error
def cf_spaces():
    command = ["cf", "spaces"]
    log_command(command)
    return subprocess.check_output(command).decode()


def cf_delete_service(service):
    command = ["cf", "delete-service", service, "-f"]
    log_command(command)
    return subprocess.check_call(command)


@log_output_on_error
def cf_get_service_guid(service):
    command = ["cf", "service", service, "--guid"]
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
    """Equal to running cf apps and cf services"""
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


def cf_api_get_space_routes(space_guid):
    logger.info("------------------ CF: get routes in space {} ------------------".format(space_guid))
    return CfApiClient.get_client().call(method="GET", path="spaces/{}/routes".format(space_guid))

def cf_api_get_space_service_brokers(space_guid):
    logger.info("------------------ CF: service brokers for space {} ------------------".format(space_guid))
    return __get_all_pages(path="service_brokers", query_params={"q": "space_guid:{}".format(space_guid)})


def cf_api_delete_route(route_guid, timeout=120):
    logger.info("------------------ CF: delete route {} ------------------".format(route_guid))
    response = CfApiClient.get_client().call(method="DELETE",
                                             path="routes/{}".format(route_guid),
                                             params={"async": True})
    if response != "":
        # routes are deleted asynchronously - to check that a route was deleted, job status is checked
        path = "jobs/{}".format(response["entity"]["guid"])
        now = time.time()
        while time.time() - now < timeout:
            response = CfApiClient.get_client().call(method="GET", path=path)
            job_status = response["entity"]["status"]
            if job_status == "finished":
                return
            logger.info("Deleting route - job status: {}".format(job_status))
            time.sleep(5)
        raise TimeoutError("Job deleting route did not finish in {}s".format(timeout))

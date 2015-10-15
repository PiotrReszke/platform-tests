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

import functools
import subprocess

from retry import retry

from . import CfApiClient, get_logger, log_command, get_config_value, TEST_SETTINGS, UnexpectedResponseError


__all__ = ["cf_login", "cf_push", "cf_create_service", "cf_delete", "cf_env", "cf_delete_service",
           "cf_api_get_service_instances", "cf_api_create_service_instance", "cf_api_get_app_env",
           "cf_api_get_space_services", "cf_api_app_summary", "cf_api_space_summary", "cf_api_get_org_spaces",
           "cf_api_get_space_routes", "cf_api_get_service_brokers", "cf_api_delete_org", "cf_api_delete_route",
           "JobFailedException"]


class JobFailedException(Exception):
    pass


# ====================================================== cf cli ====================================================== #

cli_logger = get_logger("CF CLI")

def log_output_on_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.SubprocessError as e:
            cli_logger.error(e.output.decode("utf-8"))
            raise
    return wrapper


def cf_login(organization_name, space_name):
    api_url = get_config_value("cf_endpoint")
    username = TEST_SETTINGS["TEST_USERNAME"]
    password = TEST_SETTINGS["TEST_PASSWORD"]
    command = ["cf", "login", "-a", api_url, "-u", username, "-p", password, "-o", organization_name, "-s", space_name]
    if TEST_SETTINGS["TEST_DISABLE_SSL_VALIDATION"] is True:
        command.append("--skip-ssl-validation")
    log_command(command, replace=(password, "[SECRET]"))
    subprocess.check_call(command)


@log_output_on_error
def cf_push(local_path, local_jar):
    command = ["cf", "push", "-f", local_path, "-p", local_jar]
    log_command(command)
    return subprocess.check_output(command).decode()


@log_output_on_error
def cf_create_service(broker_name, plan, instance_name):
    command = ["cf", "create-service", broker_name, plan, instance_name]
    log_command(command)
    return subprocess.check_output(command).decode()


def cf_delete(app_name):
    command = ["cf", "delete", app_name, "-f"]
    log_command(command)
    subprocess.check_call(command)


@log_output_on_error
def cf_env(app_name):
    command = ["cf", "env", app_name]
    log_command(command)
    return subprocess.check_output(command).decode()


def cf_delete_service(service):
    command = ["cf", "delete-service", service, "-f"]
    log_command(command)
    return subprocess.check_call(command)


# ====================================================== cf api ====================================================== #

def __get_all_pages(endpoint, query_params=None, log_msg=""):
    """For requests which return paginated results"""
    query_params = query_params or {}
    resources = []
    page_num = 1
    while True:
        params = {"results-per-page": 100, "page": page_num}
        params.update(query_params)
        log_msg = "{} page {}".format(log_msg, page_num)
        response = CfApiClient.get_client().request(method="GET", endpoint=endpoint, params=params, log_msg=log_msg)
        resources.extend(response["resources"])
        if page_num == response["total_pages"]:
            break
        page_num += 1
    return resources


@retry(TimeoutError, tries=10, delay=2)
def __handle_delete_request(endpoint, log_msg, async=True):
    params = {"async": str(async).lower(), "recursive": "true"}
    try:
        response = CfApiClient.get_client().request("DELETE", endpoint=endpoint, params=params, log_msg=log_msg)
    except UnexpectedResponseError as e:
        if e.status == 404:  # Deleted resource could not be found
            return
    if async:
        # Ensure that job requested asynchronously is finished within timeout
        job_id = response["entity"]["guid"]
        job_status_response = CfApiClient.get_client().request(method="GET", endpoint="jobs/{}".format(job_id),
                                                               log_msg="CF: get job status for {}".format(log_msg))
        job_status = job_status_response["entity"]["status"]
        if job_status == "finished":
            return
        if job_status == "failed":
            raise JobFailedException("Job failed")
        raise TimeoutError("Job did not finish")


# -------------------------------------------------- organizations --------------------------------------------------- #

def cf_api_get_orgs():
    """GET /v2/organizations"""
    return __get_all_pages(endpoint="organizations", log_msg="CF: get all organizations")


@retry(JobFailedException, tries=3)
def cf_api_delete_org(org_guid, async=True):
    """DELETE /v2/organizations/{org_guid}"""
    __handle_delete_request(endpoint="organizations/{}".format(org_guid), log_msg="CF: delete organization", async=async)


def cf_api_get_org_spaces(org_guid):
    """GET /v2/organizations/{org_guid}/spaces"""
    return __get_all_pages(endpoint="organizations/{}/spaces".format(org_guid), log_msg="CF: get spaces in org")


def cf_api_get_org_users(org_guid, space_guid=None):
    """GET /v2/organizations/{org_guid}/users"""
    params = {}
    if space_guid:
        params = {"space_guid": space_guid}
    return __get_all_pages(endpoint="organizations/{}/users".format(org_guid), query_params=params,
                           log_msg="CF: get users in org (space)")


# ------------------------------------------------------ spaces ------------------------------------------------------ #

def cf_api_get_spaces():
    """GET /v2/spaces"""
    return __get_all_pages(endpoint="spaces", log_msg="CF: get all spaces")


def cf_api_space_summary(space_guid):
    """GET /v2/spaces/{space_guid}/summary - Equal to running cf apps and cf services"""
    return CfApiClient.get_client().request("GET", "spaces/{}/summary".format(space_guid),
                                            log_msg="CF: get space summary")


@retry(JobFailedException, tries=3)
def cf_api_delete_space(space_guid, async=True):
    """DELETE /v2/spaces/{space_guid}"""
    __handle_delete_request(endpoint="spaces/{}".format(space_guid), log_msg="CF: delete space", async=async)


def cf_api_get_space_routes(space_guid):
    """GET /v2/spaces/{space_guid}/routes"""
    return CfApiClient.get_client().request("GET", "spaces/{}/routes".format(space_guid),
                                            log_msg="CF: get routes in space")


def cf_api_get_space_services(space_guid):
    """GET /v2/spaces/{space_guid}/services"""
    return CfApiClient.get_client().request("GET", "spaces/{}/services".format(space_guid),
                                            log_msg="CF: get space services")


# ------------------------------------------------------ users ------------------------------------------------------- #

def cf_api_get_users():
    """GET /v2/users"""
    return __get_all_pages(endpoint="users", log_msg="CF: get all users")


@retry(JobFailedException, tries=3)
def cf_api_delete_user(user_guid, async=True):
    """DELETE /v2/users/{user_guid}"""
    __handle_delete_request(endpoint="users/{}".format(user_guid), log_msg="CF: delete user", async=async)


# ------------------------------------------------ service instances ------------------------------------------------- #

def cf_api_get_service_instances(org_guid):
    """GET /v2/service_instances"""
    return __get_all_pages(endpoint="service_instances", query_params={"organization_guid": org_guid},
                           log_msg="CF: get service instances (in org)")


def cf_api_create_service_instance(instance_name, space_guid, service_plan_guid):
    """POST /v2/service_instances"""
    return CfApiClient.get_client().request(
        method="POST",
        endpoint="service_instances",
        params={"accepts_incomplete": "true"},
        body={"name": instance_name, "space_guid": space_guid, "service_plan_guid": service_plan_guid},
        log_msg="CF: create service instance"
    )


# ------------------------------------------------------- apps ------------------------------------------------------- #

def cf_api_get_app_env(app_guid):
    """GET /v2/apps/{app_guid}/env"""
    return CfApiClient.get_client().request("GET", "apps/{}/env".format(app_guid), log_msg="CF: get app env")


def cf_api_app_summary(app_guid):
    """GET /v2/apps/{app_guid}/summary"""
    return CfApiClient.get_client().request("GET", "apps/{}/summary".format(app_guid), log_msg="CF: get app summary")


@retry(JobFailedException, tries=3)
def cf_api_delete_app(app_guid, async=True):
    """DELETE /v2/apps/{app_guid}"""
    __handle_delete_request(endpoint="apps/{}".format(app_guid), log_msg="CF: delete app", async=async)


# ------------------------------------------------- service brokers -------------------------------------------------- #

def cf_api_get_service_brokers(space_guid=None):
    """GET /v2/service_brokers"""
    query_params = {}
    if space_guid is not None:
        query_params["space_guid"] = space_guid
    return __get_all_pages(endpoint="service_brokers", query_params=query_params,
                           log_msg="CF: get service brokers (in space)")


# ----------------------------------------------------- routes ------------------------------------------------------- #

@retry(JobFailedException, tries=3)
def cf_api_delete_route(route_guid, async=True):
    """DELETE /v2/routes/{route_guid}"""
    __handle_delete_request(endpoint="routes/{}".format(route_guid), log_msg="CF: delete route", async=async)

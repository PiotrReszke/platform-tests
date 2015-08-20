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

import json

from test_utils import get_logger, PlatformApiClient


logger = get_logger("Platform api calls")


# =============================================== app-launcher-helper ================================================ #


def api_get_atk_instances(org_guid, client=None):
    """GET /rest/orgs/{organization_guid}/atkinstances"""
    logger.info("------------------ Get atk instances for org {} ------------------".format(org_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/orgs/{}/atkinstances".format(org_guid))
    return response


# ======================================================== das ======================================================= #


def api_get_transfers(org_guids, query="", filters=(), size=12, time_from=0, client=None):
    """GET /rest/das/requests"""
    logger.debug("------------------ Get transfers ------------------")
    client = client or PlatformApiClient.get_admin_client()
    query_params = {
        "orgs": ",".join(org_guids),
        "query": query,
        "filters": list(filters),
        "size": size,
        "from": time_from
    }
    response = client.request("GET", "rest/das/requests", params=query_params)
    return response


def api_create_transfer(category=None, is_public=None, org_guid=None, source=None, title=None, client=None):
    """POST /rest/das/requests"""
    logger.debug("------------------ Create a transfer ------------------")
    body_keys = ["category", "publicRequest", "orgUUID", "source", "title"]
    values = [category, is_public, org_guid, source, title]
    body = {key: val for key, val in zip(body_keys, values) if val is not None}
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/das/requests", body=body)
    return response


def api_get_transfer(request_id, client=None):
    """GET /rest/das/requests/{request_id}"""
    logger.debug("------------------ Get transfer {} ------------------".format(request_id))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/das/requests/{}".format(request_id))
    return response


def api_delete_transfer(request_id, client=None):
    """DELETE /rest/das/requests/{request_id}"""
    logger.debug("------------------ Delete transfer {} ------------------".format(request_id))
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/das/requests/{}".format(request_id))


# =================================================== data-catalog =================================================== #


def api_get_datasets(org_guid_list, query="", filters=(), size=12, time_from=0, only_private=False,
                     only_public=False, client=None):
    """GET /rest/datasets"""
    logger.debug("------------------ Get list of data sets in orgs {} ------------------".format(org_guid_list))
    query_params = {
        "orgs": ",".join(org_guid_list),
        "query": json.dumps({"query": query, "filters": list(filters), "size": size, "from": time_from})
    }
    if only_private:
        query_params["onlyPrivate"] = only_private
    if only_public:
        query_params["onlyPublic"] = only_public
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/datasets", params=query_params)
    return response


def api_get_dataset(entry_id, client=None):
    """GET /rest/datasets/{entry_id}"""
    logger.debug("------------------ Get data set {} ------------------".format(entry_id))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/datasets/{}".format(entry_id))
    return response


def api_delete_dataset(entry_id, client=None):
    """DELETE /rest/datasets/{entry_id}"""
    logger.debug("------------------ Delete data set {} ------------------".format(entry_id))
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/datasets/{}".format(entry_id))


def api_update_dataset(entry_id, creation_time=None, target_uri=None, category=None, format=None,
                       record_count=None, is_public=None, org_guid=None, source_uri=None, size=None, data_sample=None,
                       title=None, client=None):
    """POST /rest/datasets/{entry_id}"""
    logger.debug("------------------ Update data set {} ------------------".format(entry_id))
    values = [creation_time, target_uri, category, format, record_count, is_public, org_guid, source_uri, size,
              data_sample, title]
    body_keys = ["creationTime", "targetUri", "category", "format", "recordCount", "isPublic", "orgUUID", "sourceUri",
                 "size", "dataSample", "title"]
    body = {k: v for k, v in zip(body_keys, values) if v is not None}
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/datasets/{}".format(entry_id), body=body)
    return response


def api_put_dataset_in_index(entry_id, creation_time=None, target_uri=None, category=None, format=None,
                             record_count=None, is_public=None, org_guid=None, source_uri=None, size=None,
                             data_sample=None, title=None, client=None):
    """PUT /rest/datasets/{entry_id}"""
    logger.debug("------------------ Put data set {} in index ------------------".format(entry_id))
    values = [creation_time, target_uri, category, format, record_count, is_public, org_guid, source_uri, size,
              data_sample, title]
    body_keys = ["creationTime", "targetUri", "category", "format", "recordCount", "isPublic", "orgUUID", "sourceUri",
                 "size", "dataSample", "title"]
    body = {k: v for k, v in zip(body_keys, values) if v is not None}
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("PUT", "rest/datasets/{}".format(entry_id), body=body)
    return response


def api_get_dataset_count(org_guid_list, only_private, only_public, client=None):
    """GET /rest/datasets/count"""
    logger.debug("------------------ Get data set count in orgs ------------------".format(org_guid_list))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/datasets/count")
    return response


# ================================================== file-server ===================================================== #


def api_get_atk_client_file_name(client=None):
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "files/atkclient")
    return response["file"]


def api_get_file(source_file_name, target_file_path, client=None):
    client = client or PlatformApiClient.get_admin_client()
    client.download_file(endpoint="files/{}".format(source_file_name), target_file_path=target_file_path)


# ============================================= hive / dataset-publisher ============================================= #


def api_publish_dataset(category, creation_time, data_sample, format, is_public,
                        org_guid, record_count, size, source_uri, target_uri, title, client=None):
    """POST /rest/tables"""
    logger.info("------------------ Publish dataset {} in hive ------------------".format(title))
    client = client or PlatformApiClient.get_admin_client()
    body = {"category": category, "creationTime": creation_time, "dataSample": data_sample, "format": format,
            "isPublic": is_public, "orgUUID": org_guid, "recordCount": record_count, "size": size,
            "sourceUri": source_uri, "targetUri": target_uri, "title": title}
    response = client.request("POST", "rest/tables", body=body)
    return response


# ============================================== latest-events-service =============================================== #


def api_get_latest_events(client):
    """GET /rest/les/events"""
    logger.debug("------------------ Get latest events ------------------")
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/les/events")
    return response


# ================================================= metrics-provider ================================================= #


def api_get_org_metrics(org_guid, client=None):
    """GET /rest/orgs/{org_guid}/metrics"""
    logger.debug("------------------ Get metrics for organization {} ------------------".format(org_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/orgs/{}/metrics".format(org_guid))
    return response


# ================================================= service-catalog ================================================== #


def api_get_marketplace_services(space_guid, client=None):
    """GET /rest/services"""
    logger.debug("------------------ Get marketplace services ------------------")
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/services", params={"space": space_guid})
    return response["resources"]


def api_get_service(service_guid, client=None):
    """GET /rest/service/{service_guid}"""
    logger.debug("------------------ Get service {} ------------------".format(service_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/service/{}".format(service_guid))
    return response


def api_get_service_instances(space_guid, service_guid=None, client=None):
    """GET /rest/service_instances"""
    logger.debug("--------------- Get service instances for service {} in space {} ---------------".format(service_guid,
                                                                                                           space_guid))
    client = client or PlatformApiClient.get_admin_client()
    query_params = {"space": space_guid}
    if service_guid is not None:
        query_params["broker"] = service_guid
    response = client.request("GET", "rest/service_instances", params=query_params)
    return response


def api_create_service_instance(name, service_plan_guid, org_guid, space_guid, client=None):
    """POST /rest/service_instances"""
    logger.debug("----------------- Create service instance {} in space {} -----------------".format(name, space_guid))
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "name": name,
        "organization_guid": org_guid,
        "service_plan_guid": service_plan_guid,
        "space_guid": space_guid,
        "parameters": {"name": name}
    }
    response = client.request("POST", "rest/service_instances", body=body)
    return response


def api_delete_service_instance(service_instance_guid, client):
    """DELETE /rest/service_instances/{service_instance_guid}"""
    logger.debug("------------------ Delete service instance {} ------------------".format(service_instance_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("DELETE", "rest/service_instances/{}".format(service_instance_guid))
    return response


# ----------------------------------------------- Applications ----------------------------------------------- #

def api_get_filtered_applications(space, service_label=None, client=None):
    """GET /rest/apps"""
    logger.info("------------------ Get applications in space {} ------------------".format(space))
    client = client or PlatformApiClient.get_admin_client()
    query_params = {"space": space}
    if service_label is not None:
        query_params["service_label"] = service_label
    response = client.request("GET", "rest/apps", params=query_params)
    return response


def api_get_app_summary(app_guid, client=None):
    """GET /rest/apps/{app_guid}"""
    logger.debug("------------------ Get {} details ------------------".format(app_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/apps/{}".format(app_guid))
    return response

def api_delete_app(app_guid, cascade=True, client=None):
    """DELETE /rest/apps/{app_guid}"""
    logger.debug("------------------ Delete app {} ------------------".format(app_guid))
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/apps/{}".format(app_guid))


def api_get_app_orphan_services(app_guid, client=None):
    """GET /rest/apps/{app_guid}/orphan_services"""
    logger.debug("------------------ Retrieve orphan services fo app {} ------------------".format(app_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/apps/{}/orphan_services".format(app_guid))
    return response


def api_change_app_status(app_guid, status, client=None):
    """POST /rest/apps/{app_guid}/status"""
    logger.debug("------------------ Restage app {} ------------------".format(app_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/apps/{}/status".format(app_guid), body={"name": status})
    return response


def api_get_app_bindings(app_guid, client=None):
    """GET /rest/apps/{app_guid}/service_bindings"""
    logger.debug("----------------- Get bindings of app {}-----------------".format(app_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/apps/{}/service_bindings".format(app_guid))
    return response["resources"]


def api_create_service_binding(app_guid, service_instance_guid, client=None):
    """POST /rest/apps/{app_guid}/service_bindings"""
    logger.debug("---------- Create binding for app {} to service instance {} ----------".format(app_guid,
                                                                                                 service_instance_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "apps/{}/service_bindings".format(app_guid),
                              body={"rest/service_instance_guid": service_instance_guid})
    return response


def api_delete_service_binding(binding_guid, client=None):
    """DELETE /rest/service_bindings/{binding_guid}"""
    logger.debug("------------------ Delete binding {} ------------------".format(binding_guid))
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/service_bindings/{}".format(binding_guid))


def api_create_scoring_engine(atk_name, instance_name, space_guid, service_plan_guid, client=None):
    """POST /rest/orgs/atk/scoring-engine"""
    logger.debug("------------------ Create scoring engine for atk {} ------------------".format(atk_name))
    client = client or PlatformApiClient.get_admin_client()
    raise NotImplementedError("Please implement this method if you need it")


# ================================================= user-management ================================================== #


def api_get_organizations(client=None):
    """GET /rest/orgs"""
    logger.debug("------------------ Get organizations ------------------")
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/orgs")
    return response


def api_create_organization(name, client=None):
    """POST /rest/orgs"""
    logger.debug("------------------ Create organization with name {} ------------------".format(name))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/orgs", body={"name": name})
    return response.strip('"')  # guid is returned together with quotation marks


def api_delete_organization(org_guid, client=None):
    """DELETE /rest/orgs/{organization_guid}"""
    logger.debug("------------------ Delete organization {} ------------------".format(org_guid))
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/orgs/{}".format(org_guid))


def api_rename_organization(org_guid, new_name, client=None):
    """PUT /rest/orgs/{organization_guid}/name"""
    logger.debug("------------------ Rename organization {} to {} ------------------".format(org_guid, new_name))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("PUT", "rest/orgs/{}/name".format(org_guid), body={"name": new_name})
    return response


def api_add_organization_user(org_guid, username, roles=(), client=None):
    """POST /rest/orgs/{organization_guid}/users"""
    logger.debug("------------------ Add user {} to organization {} ------------------".format(username, org_guid))
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": list(roles)
    }
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/orgs/{}/users".format(org_guid), body=body)
    return response


def api_get_organization_users(org_guid, client=None):
    """GET /rest/orgs/{organization_guid}/users"""
    logger.debug("------------------ Get users from organization {} ------------------".format(org_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/orgs/{}/users".format(org_guid))
    return response


def api_delete_organization_user(org_guid, user_guid, client=None):
    """DELETE /rest/orgs/{organization_guid}/users/{user_guid}"""
    logger.debug("------------------ Delete user {} from organization {} ------------------".format(user_guid, org_guid))
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/orgs/{}/users/{}".format(org_guid, user_guid))


def api_update_organization_user(org_guid, user_guid, new_roles=None, client=None):
    """PUT /rest/orgs/{organization_guid}/users/{user_guid}"""
    logger.debug("------------------ Update user {} from organization {} ------------------".format(user_guid, org_guid))
    client = client or PlatformApiClient.get_admin_client()
    body = {"guid": org_guid}
    if new_roles is not None:
        body["roles"] = new_roles
    response = client.request("PUT", "rest/orgs/{}/users/{}".format(org_guid, user_guid), body=body)
    return response


def api_create_space_user(org_guid, space_guid, username, roles=(), client=None):
    """POST /rest/spaces/{space_guid}/users"""
    logger.debug("------------------ Create user {} in space {} ------------------".format(username, space_guid))
    client = client or PlatformApiClient.get_admin_client()
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": list(roles)
    }
    response = client.request("POST", "rest/spaces/{}/users".format(space_guid), body=body)
    return response


def api_get_space_users(space_guid, client=None):
    """GET /rest/spaces/{space_guid}/users"""
    logger.debug("------------------ Get users from space {} ------------------".format(space_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/spaces/{}/users".format(space_guid))
    return response


def api_delete_space_user(space_guid, user_guid, client=None):
    """DELETE /rest/spaces/{space_guid}/users/{user_guid}"""
    logger.debug("------------------ Delete user {} from space {} ------------------".format(user_guid, space_guid))
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/spaces/{}/users/{}".format(space_guid, user_guid))


def api_update_space_user(org_guid, space_guid, user_guid, new_username=None, new_roles=None, client=None):
    """PUT /rest/spaces/{space_guid}/users/{user_guid}"""
    logger.debug("------------------ Update user {} from space {} ------------------".format(user_guid, space_guid))
    client = client or PlatformApiClient.get_admin_client()
    body = {"org_guid": org_guid}
    if new_username is not None:
        body["username"] = new_username
    if new_roles is not None:
        body["roles"] = new_roles
    response = client.request("PUT", "rest/spaces/{}/users/{}".format(space_guid, user_guid), body=body)
    return response


def api_invite_user(email, client=None):
    """POST /rest/invitations"""
    logger.debug("-------------------- Invite user {} --------------------".format(email))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/invitations", body={"email": email})
    return response


def api_register_new_user(code, password, org_name=None, client=None):
    """POST /rest/registrations"""
    logger.debug("--------------- Register organization {} with password {} ---------------".format(org_name, password))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/registrations", params={"code": code},
                              body={"org": org_name, "password": password})
    return response


def api_get_spaces_in_org(org_guid, client=None):
    """GET /rest/orgs/{org}/spaces"""
    logger.info("------------------ Get spaces in org {} ------------------".format(org_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/orgs/{}/spaces".format(org_guid))
    if "resources" in response:
        return response["resources"]
    return response


def api_get_spaces(client=None):
    """GET /rest/spaces"""
    logger.info("------------------ Get all spaces ------------------")
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("GET", "rest/spaces")
    return response


def api_create_space(org_guid, name, client=None):
    """POST /rest/spaces"""
    logger.info("------------------ Create space {} at organization {} ------------------".format(name, org_guid))
    client = client or PlatformApiClient.get_admin_client()
    response = client.request("POST", "rest/spaces", body={"name": name, "org_guid": org_guid})
    # if response == "":
    #     raise AssertionError("Response to POST /rest/spaces did not return space guid.")
    return response


def api_delete_space(space_guid, client=None):
    """DELETE /rest/spaces/{space}"""
    logger.info("------------------ Delete space {} ------------------".format(space_guid))
    client = client or PlatformApiClient.get_admin_client()
    client.request("DELETE", "rest/spaces/{}".format(space_guid))


from test_utils.api_client import ApiClient
from test_utils.logger import get_logger


logger = get_logger("user management calls")


__CLIENT = None

def __get_api_client():
    global __CLIENT
    if __CLIENT is None:
        __CLIENT = ApiClient(application="user-management")
    return __CLIENT

# ------------------------------------- Orgs Controller ------------------------------------- #

def api_get_organizations():
    """GET /rest/orgs"""
    logger.info("------------------ Get organizations ------------------")
    return __get_api_client().call("get_organizations")


def api_create_organization(name):
    """POST /rest/orgs"""
    logger.info("------------------ Create organization with name {} ------------------".format(name))
    return __get_api_client().call("create_organization", body={"name": name})


def api_delete_organization(org_guid):
    """DELETE /rest/orgs/{organization_guid}"""
    logger.info("------------------ Delete organization {} ------------------".format(org_guid))
    return __get_api_client().call("delete_organization", organization_guid=org_guid)


def api_rename_organization(org_guid, new_name):
    """PUT /rest/orgs/{organization_guid}/name"""
    logger.info("------------------ Rename organization {} to {} ------------------".format(org_guid, new_name))
    return __get_api_client().call("rename_organization", organization_guid=org_guid, body={"name": new_name})


# ------------------------------------- Users Controller ------------------------------------- #

def api_create_organization_user(org_guid, username, roles=None):
    """POST /rest/orgs/{organization_guid}/users"""
    logger.info("------------------ Create user {} in organization {} ------------------".format(username, org_guid))
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": [] if roles is None else roles
    }
    return __get_api_client().call("create_organization_user", organization_guid=org_guid, body=body)


def api_get_organization_users(org_guid):
    """GET /rest/orgs/{organization_guid}/users"""
    logger.info("------------------ Get users from organization {} ------------------".format(org_guid))
    return __get_api_client().call("get_organization_users", organization_guid=org_guid)


def api_delete_organization_user(org_guid, user_guid):
    """DELETE /rest/orgs/{organization_guid}/users/{user_guid}"""
    logger.info("------------------ Delete user {} from organization {} ------------------".format(user_guid, org_guid))
    return __get_api_client().call("delete_organization_user", organization_guid=org_guid, user_guid=user_guid)


def api_update_organization_user(org_guid, user_guid, new_roles=None):
    """PUT /rest/orgs/{organization_guid}/users/{user_guid}"""
    logger.info("------------------ Update user {} from organization {} ------------------".format(user_guid, org_guid))
    body = {
        "org_guid": org_guid
    }
    if new_roles is not None:
        body["roles"] = new_roles
    return __get_api_client().call("update_organization_user", organization_guid=org_guid, user_guid=user_guid, body=body)


def api_create_space_user(org_guid, space_guid, username, roles=None):
    """POST /rest/spaces/{space_guid}/users"""
    logger.info("------------------ Create user {} in space {} ------------------".format(username, space_guid))
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": [] if roles is None else roles
    }
    return __get_api_client().call("create_space_user", space_guid=space_guid, body=body)


def api_get_space_users(space_guid):
    """GET /rest/spaces/{space_guid}/users"""
    logger.info("------------------ Get users from space {} ------------------".format(space_guid))
    return __get_api_client().call("get_space_users", space_guid=space_guid)


def api_delete_space_user(space_guid, user_guid):
    """DELETE /rest/spaces/{space_guid}/users/{user_guid}"""
    logger.info("------------------ Delete user {} from space {} ------------------".format(user_guid, space_guid))
    return __get_api_client().call("delete_space_user", space_guid=space_guid, user_guid=user_guid)


def api_update_space_user(org_guid, space_guid, user_guid, new_username=None, new_roles=None):
    """PUT /rest/spaces/{space_guid}/users/{user_guid}"""
    logger.info("------------------ Update user {} from space {} ------------------".format(user_guid, space_guid))
    body = {
        "org_guid": org_guid
    }
    if new_username is not None:
        body["username"] = new_username
    if new_roles is not None:
        body["roles"] = new_roles
    return __get_api_client().call("update_space_user", space_guid=space_guid, user_guid=user_guid, body=body)



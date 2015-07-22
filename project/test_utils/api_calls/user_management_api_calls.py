from ..logger import get_logger


logger = get_logger("user management calls")


APP_NAME = "user-management"


# ------------------------------------- Orgs Controller ------------------------------------- #
def api_get_organizations(client):
    """GET /rest/orgs"""
    logger.info("------------------ Get organizations ------------------")
    return client.call(APP_NAME, "get_organizations")


def api_create_organization(client, name):
    """POST /rest/orgs"""
    logger.info("------------------ Create organization with name {} ------------------".format(name))
    return client.call(APP_NAME, "create_organization", body={"name": name})


def api_delete_organization(client, org_guid):
    """DELETE /rest/orgs/{organization_guid}"""
    logger.info("------------------ Delete organization {} ------------------".format(org_guid))
    return client.call(APP_NAME, "delete_organization", organization_guid=org_guid)


def api_rename_organization(client, org_guid, new_name):
    """PUT /rest/orgs/{organization_guid}/name"""
    logger.info("------------------ Rename organization {} to {} ------------------".format(org_guid, new_name))
    return client.call(APP_NAME, "rename_organization", organization_guid=org_guid, body={"name": new_name})


# ------------------------------------- Users Controller ------------------------------------- #

def api_create_organization_user(client, org_guid, username, roles=None):
    """POST /rest/orgs/{organization_guid}/users"""
    logger.info("------------------ Create user {} in organization {} ------------------".format(username, org_guid))
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": [] if roles is None else roles
    }
    return client.call(APP_NAME, "create_organization_user", organization_guid=org_guid, body=body)


def api_get_organization_users(client, org_guid):
    """GET /rest/orgs/{organization_guid}/users"""
    logger.info("------------------ Get users from organization {} ------------------".format(org_guid))
    return client.call(APP_NAME, "get_organization_users", organization_guid=org_guid)


def api_delete_organization_user(client, org_guid, user_guid):
    """DELETE /rest/orgs/{organization_guid}/users/{user_guid}"""
    logger.info("------------------ Delete user {} from organization {} ------------------".format(user_guid, org_guid))
    return client.call(APP_NAME, "delete_organization_user", organization_guid=org_guid, user_guid=user_guid)


def api_update_organization_user(client, org_guid, user_guid, new_roles=None):
    """PUT /rest/orgs/{organization_guid}/users/{user_guid}"""
    logger.info("------------------ Update user {} from organization {} ------------------".format(user_guid, org_guid))
    body = {
        "org_guid": org_guid
    }
    if new_roles is not None:
        body["roles"] = new_roles
    return client.call(APP_NAME, "update_organization_user", organization_guid=org_guid, user_guid=user_guid, body=body)


def api_create_space_user(client, org_guid, space_guid, username, roles=None):
    """POST /rest/spaces/{space_guid}/users"""
    logger.info("------------------ Create user {} in space {} ------------------".format(username, space_guid))
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": [] if roles is None else roles
    }
    return client.call(APP_NAME, "create_space_user", space_guid=space_guid, body=body)


def api_get_space_users(client, space_guid):
    """GET /rest/spaces/{space_guid}/users"""
    logger.info("------------------ Get users from space {} ------------------".format(space_guid))
    return client.call(APP_NAME, "get_space_users", space_guid=space_guid)


def api_delete_space_user(client, space_guid, user_guid):
    """DELETE /rest/spaces/{space_guid}/users/{user_guid}"""
    logger.info("------------------ Delete user {} from space {} ------------------".format(user_guid, space_guid))
    return client.call(APP_NAME, "delete_space_user", space_guid=space_guid, user_guid=user_guid)


def api_update_space_user(client, org_guid, space_guid, user_guid, new_username=None, new_roles=None):
    """PUT /rest/spaces/{space_guid}/users/{user_guid}"""
    logger.info("------------------ Update user {} from space {} ------------------".format(user_guid, space_guid))
    body = {
        "org_guid": org_guid
    }
    if new_username is not None:
        body["username"] = new_username
    if new_roles is not None:
        body["roles"] = new_roles
    return client.call(APP_NAME, "update_space_user", space_guid=space_guid, user_guid=user_guid, body=body)



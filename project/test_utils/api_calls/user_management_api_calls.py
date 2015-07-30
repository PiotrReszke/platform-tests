from test_utils.logger import get_logger


APP_NAME = "user-management"
logger = get_logger("user-management calls")


# ------------------------------------- Orgs Controller ------------------------------------- #
def api_get_organizations(client):
    """GET /rest/orgs"""
    logger.debug("------------------ Get organizations ------------------")
    return client.call(APP_NAME, "get_organizations")


def api_create_organization(client, name):
    """POST /rest/orgs"""
    logger.debug("------------------ Create organization with name {} ------------------".format(name))
    return client.call(APP_NAME, "create_organization", body={"name": name})


def api_delete_organization(client, org_guid):
    """DELETE /rest/orgs/{organization_guid}"""
    logger.debug("------------------ Delete organization {} ------------------".format(org_guid))
    return client.call(APP_NAME, "delete_organization", organization_guid=org_guid)


def api_rename_organization(client, org_guid, new_name):
    """PUT /rest/orgs/{organization_guid}/name"""
    logger.debug("------------------ Rename organization {} to {} ------------------".format(org_guid, new_name))
    return client.call(APP_NAME, "rename_organization", organization_guid=org_guid, body={"name": new_name})


# ------------------------------------- Users Controller ------------------------------------- #

def api_create_organization_user(client, org_guid, username, roles=None):
    """POST /rest/orgs/{organization_guid}/users"""
    logger.debug("------------------ Create user {} in organization {} ------------------".format(username, org_guid))
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": [] if roles is None else roles
    }
    return client.call(APP_NAME, "create_organization_user", organization_guid=org_guid, body=body)


def api_get_organization_users(client, org_guid):
    """GET /rest/orgs/{organization_guid}/users"""
    logger.debug("------------------ Get users from organization {} ------------------".format(org_guid))
    return client.call(APP_NAME, "get_organization_users", organization_guid=org_guid)


def api_delete_organization_user(client, org_guid, user_guid):
    """DELETE /rest/orgs/{organization_guid}/users/{user_guid}"""
    logger.debug("------------------ Delete user {} from organization {} ------------------".format(user_guid, org_guid))
    return client.call(APP_NAME, "delete_organization_user", organization_guid=org_guid, user_guid=user_guid)


def api_update_organization_user(client, org_guid, user_guid, new_roles=None):
    """PUT /rest/orgs/{organization_guid}/users/{user_guid}"""
    logger.debug("------------------ Update user {} from organization {} ------------------".format(user_guid, org_guid))
    body = {
        "org_guid": org_guid
    }
    if new_roles is not None:
        body["roles"] = new_roles
    return client.call(APP_NAME, "update_organization_user", organization_guid=org_guid, user_guid=user_guid, body=body)


def api_create_space_user(client, org_guid, space_guid, username, roles=None):
    """POST /rest/spaces/{space_guid}/users"""
    logger.debug("------------------ Create user {} in space {} ------------------".format(username, space_guid))
    body = {
        "username": username,
        "org_guid": org_guid,
        "roles": [] if roles is None else roles
    }
    return client.call(APP_NAME, "create_space_user", space_guid=space_guid, body=body)


def api_get_space_users(client, space_guid):
    """GET /rest/spaces/{space_guid}/users"""
    logger.debug("------------------ Get users from space {} ------------------".format(space_guid))
    return client.call(APP_NAME, "get_space_users", space_guid=space_guid)


def api_delete_space_user(client, space_guid, user_guid):
    """DELETE /rest/spaces/{space_guid}/users/{user_guid}"""
    logger.debug("------------------ Delete user {} from space {} ------------------".format(user_guid, space_guid))
    return client.call(APP_NAME, "delete_space_user", space_guid=space_guid, user_guid=user_guid)


def api_update_space_user(client, org_guid, space_guid, user_guid, new_username=None, new_roles=None):
    """PUT /rest/spaces/{space_guid}/users/{user_guid}"""
    logger.debug("------------------ Update user {} from space {} ------------------".format(user_guid, space_guid))
    body = {
        "org_guid": org_guid
    }
    if new_username is not None:
        body["username"] = new_username
    if new_roles is not None:
        body["roles"] = new_roles
    return client.call(APP_NAME, "update_space_user", space_guid=space_guid, user_guid=user_guid, body=body)


# ------------------------------------- Registrations Controller ------------------------------------- #

def api_invite_user(client, email):
    """POST /rest/invitations"""
    logger.debug("-------------------- Invite user {} --------------------".format(email))
    body = {
        "email": email
    }
    return client.call(APP_NAME, "invite_user", body=body)


def api_register_org_and_user(client, code, org_name, password):
    """POST /rest/registrations"""
    logger.debug("--------------- Register organization {} with password {} ---------------".format(org_name, password))
    body = {
        "org": org_name,
        "password": password
    }
    return client.call(APP_NAME, "register_org_and_user", code=code, body=body)


# ------------------------------------- Spaces Controller ------------------------------------- #

def api_get_spaces_in_org(client, org_guid):
    """GET /rest/orgs/{org}/spaces"""
    logger.info("------------------ Get spaces in  org {} ------------------".format(org_guid))
    return client.call(APP_NAME, "get_spaces_in_org", org=org_guid)

def api_get_spaces(client):
    """GET /rest/spaces"""
    logger.info("------------------ Get all spaces ------------------")
    return client.call(APP_NAME, "get_spaces")

def api_create_space(client, name, org_guid):
    """POST /rest/spaces"""
    logger.info("------------------ Create space with name {} ------------------".format(name))
    return client.call(APP_NAME, "create_space", body={"name": name, "org_guid": org_guid})

def api_delete_space(client, space=None):
    """DELETE /rest/spaces/{space}"""
    logger.info("------------------ Delete space {} ------------------".format(space))
    return client.call(APP_NAME, "delete_space", space=space)

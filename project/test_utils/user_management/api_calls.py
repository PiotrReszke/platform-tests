from test_utils.api_client import ApiClient
from test_utils.logger import get_logger


logger = get_logger("user management calls")


__CLIENT = None

def __get_api_client():
    global __CLIENT
    if __CLIENT is None:
        __CLIENT = ApiClient(application="user-management")
    return __CLIENT

# --------------------------------------- Orgs Controller --------------------------------------- #

def api_get_organizations():
    """GET /rest/orgs"""
    logger.info("-------------------- Get organizations --------------------")
    return __get_api_client().call("get_organizations")


def api_create_organization(name):
    """POST /rest/orgs"""
    logger.info("-------------------- Create organization with name {} --------------------".format(name))
    return __get_api_client().call("create_organization", body={"name": name})


def api_delete_organization(guid):
    """DELETE /rest/orgs/{organization_guid}"""
    logger.info("-------------------- Delete organization {} --------------------".format(guid))
    return __get_api_client().call("delete_organization", organization_guid=guid)


def api_rename_organization(guid, new_name):
    """PUT /rest/orgs/{organization_guid}/name"""
    logger.info("-------------------- Rename organization {} to {} --------------------".format(guid, new_name))
    return __get_api_client().call("rename_organization", organization_guid=guid, body={"name": new_name})


from test_utils.logger import get_logger
import json

logger = get_logger("service-catalog calls")

APP_NAME = "service-catalog"

def api_get_marketplace_services(client, space_guid):
    """GET /rest/services"""
    logger.info("------------------ Get marketplace services ------------------")
    return client.call(APP_NAME, "get_marketplace_services", space=space_guid)


def api_get_apps(space_guid):
    """GET /rest/orgs"""
    logger.info("------------------ Get applications list from space {} ------------------".format(space_guid))
    return json.loads(get_app_client().call(APP_NAME, "get_apps_list", space=space_guid))


def api_get_app_details(app_guid):
    """POST /rest/orgs"""
    logger.info("------------------ Get {} details ------------------".format(app_guid))
    return json.loads(get_app_client().call(APP_NAME, "get_app_details", app_guid=app_guid))

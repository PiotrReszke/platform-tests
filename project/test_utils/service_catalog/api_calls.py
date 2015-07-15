from test_utils.api_client import get_app_client
from test_utils.logger import get_logger


logger = get_logger("service-catalog calls")

APP_NAME = "service-catalog"

def api_get_marketplace_services(space_guid):
    """GET /rest/services"""
    logger.info("------------------ Get marketplace services ------------------")
    return get_app_client().call(APP_NAME, "get_marketplace_services", space=space_guid)


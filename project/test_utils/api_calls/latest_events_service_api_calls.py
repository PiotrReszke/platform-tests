from test_utils.logger import get_logger

APP_NAME = "latest-events-service"
logger = get_logger("latest-events-service calls")


def api_get_latest_events(client):
    """GET /rest/les/events"""
    logger.debug("------------------ Get latest events ------------------")
    return client.call(APP_NAME, "get_latest_events")

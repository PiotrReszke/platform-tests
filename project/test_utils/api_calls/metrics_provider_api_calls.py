from test_utils.logger import get_logger

APP_NAME = "metrics-provider"
logger = get_logger("metrics-provider calls")


def api_get_org_metrics(client, org_guid):
    """GET /rest/orgs/{org_guid}/metrics"""
    logger.debug("------------------ Get metrics for organization {} ------------------".format(org_guid))
    return client.call(APP_NAME, "get_org_metrics", org_guid=org_guid)

from test_utils.logger import get_logger


logger = get_logger("metrics provider calls")


APP_NAME = "metrics-provider"


def api_get_org_metrics(client, org_guid):
    """GET /rest/orgs/{org_guid}/metrics"""
    logger.info("------------------ Get metrics for organization {} ------------------".format(org_guid))
    return client.call(APP_NAME, "get_org_metrics", org_guid=org_guid)

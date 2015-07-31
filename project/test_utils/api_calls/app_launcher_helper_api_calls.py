from test_utils import get_logger


APP_NAME = "app-launcher-helper"
logger = get_logger("app-launcher-helper calls")


def api_get_atk_instances(client, org_guids):
    """GET /rest/orgs/{organization_guid}/atkinstances"""
    logger.info("------------------ Get atk instances for orgs {} ------------------".format(org_guids))
    return client.call(APP_NAME, "get_atk_instances", organization_guid=org_guids)

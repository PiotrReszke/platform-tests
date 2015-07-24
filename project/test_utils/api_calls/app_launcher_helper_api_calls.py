from test_utils import get_logger


APP_NAME = ["app-launcher-helper"]
logger = get_logger("app-launcher-helper calls")


def api_list_atk_instances(client, org_guid):
    """GET /rest/orgs/{org_guid}/atkinstances"""
    logger.debug("------------------ Get list of atk instances in org {} ------------------".format(org_guid))
    raise NotImplementedError("Please create a schema in app_launcher_helper_swagger.json")

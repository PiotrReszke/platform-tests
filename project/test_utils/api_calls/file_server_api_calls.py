from ..logger import get_logger

logger = get_logger("files calls")

APP_NAME = "file-server"

def api_get_atkfilename(client):
    """GET /files/atkclient"""
    logger.info("------------------ Get atk file name ------------------")
    return client.call(APP_NAME, "get_atkclient_name")



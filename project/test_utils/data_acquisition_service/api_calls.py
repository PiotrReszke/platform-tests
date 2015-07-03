from test_utils.api_client import ApiClient
from test_utils.logger import get_logger


logger = get_logger("das calls")


__CLIENT = None

def __get_api_client():
    global __CLIENT
    if __CLIENT is None:
        __CLIENT = ApiClient(application_name="das")
    return __CLIENT


def api_get_requests():
    """GET /rest/das/requests"""
    logger.info("------------------ Get requests ------------------")
    return __get_api_client().call("get_requests")


def api_create_request(category=None, id=None, id_in_object_store=None, is_public=None, org_guid=None, source=None,
                       state=None, token=None, timestamps=None, title=None, user_id=None):
    """POST /rest/das/requests"""
    logger.info("------------------ Create a request ------------------")
    body_keys = ["category", "id", "idInObjectStore", "publicRequest", "orgUUID", "source", "state", "token",
                 "timestamps", "title", "userId"]
    values = [category, id, id_in_object_store, is_public, org_guid, source, state, token, timestamps, title, user_id]
    body = {key: val for key, val in zip(body_keys, values) if val is not None}
    return __get_api_client().call("create_request", body=body)


def api_get_request(request_id):
    """GET /rest/das/requests/{request_id}"""
    return __get_api_client().call("get_request", request_id=request_id)


def api_delete_request(request_id):
    """DELETE /rest/das/requests/{request_id}"""
    return __get_api_client().call("delete_request", request_id=request_id)

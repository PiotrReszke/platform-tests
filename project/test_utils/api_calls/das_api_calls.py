from ..logger import get_logger


logger = get_logger("das calls")


APP_NAME = "das"


def api_get_das_requests(client, org_guids):
    """GET /rest/das/requests"""
    logger.info("------------------ Get requests ------------------")
    org_guids = ",".join(org_guids)
    return client.call(APP_NAME, "get_requests", orgs=org_guids)


def api_create_das_request(client, category=None, id=None, id_in_object_store=None, is_public=None, org_guid=None, source=None,
                           state=None, token=None, timestamps=None, title=None, user_id=None):
    """POST /rest/das/requests"""
    logger.info("------------------ Create a request ------------------")
    body_keys = ["category", "id", "idInObjectStore", "publicRequest", "orgUUID", "source", "state", "token",
                 "timestamps", "title", "userId"]
    values = [category, id, id_in_object_store, is_public, org_guid, source, state, token, timestamps, title, user_id]
    body = {key: val for key, val in zip(body_keys, values) if val is not None}
    return client.call(APP_NAME, "create_request", body=body)


def api_get_das_request(client, request_id):
    """GET /rest/das/requests/{request_id}"""
    logger.info("------------------ Get request {} ------------------".format(request_id))
    return client.call(APP_NAME, "get_request", request_id=request_id)


def api_delete_das_request(client, request_id):
    """DELETE /rest/das/requests/{request_id}"""
    logger.info("------------------ Delete request {} ------------------".format(request_id))
    return client.call(APP_NAME, "delete_request", request_id=request_id)

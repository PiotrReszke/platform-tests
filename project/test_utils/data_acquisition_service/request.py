import test_utils.data_acquisition_service.api_calls as api


class Request(object):

    def __init__(self, category=None, id=None, id_in_object_store=None, is_public=None, org_guid=None, source=None,
                 state=None, token=None, timestamps=None, title=None, user_id=None):
        self.category = category
        self.id = id
        self.id_in_object_store = id_in_object_store
        self.is_public = is_public
        self.organization_guid = org_guid
        self.source = source
        self.state = state
        self.token = token
        self.timestamps = timestamps
        self.title = title
        self.user_id = user_id

    @classmethod
    def _from_api_response(cls, api_response):
        return cls(category=api_response["category"], id=api_response["id"],
                   id_in_object_store=api_response["idInObjectStore"], is_public=api_response["is_public"],
                   org_guid=api_response["org_guid"], source=api_response["source"], state=api_response["state"],
                   token=api_response["token"], timestamps=["timestamps"], title=api_response["title"],
                   user_id=api_response["user_id"])

    @classmethod
    def create(cls, category=None, is_public=None, org_guid=None, source=None, title=None, user_id=None):
        api_response = api.api_create_request(category=category, is_public=is_public, org_guid=org_guid, source=source,
                                              title=title, user_id=user_id)
        return cls(category=category, id=api_response["id"], id_in_object_store=api_response["idInObjectStore"],
                   is_public=is_public, org_guid=org_guid, source=source, state=api_response["state"],
                   token=api_response["token"], timestamps=["timestamps"], title=title, user_id=user_id)

    @classmethod
    def get_list(cls):
        api_response = api.api_get_requests()
        requests = []
        for request_data in api_response:
            requests.append(cls._from_api_response(request_data))
        return requests

    @classmethod
    def get(cls, request_id):
        api_response = api.api_get_request(request_id)
        return cls._from_api_response(api_response)

    def delete(self):
        return api.api_delete_request(self.id)
import functools
import time

import test_utils.api_calls.das_api_calls as api
from test_utils.objects.user import get_admin_client


__all__ = ["Transfer"]


@functools.total_ordering
class Transfer(object):
    COMPARABLE_ATTRIBUTES = ["category", "id", "id_in_object_store", "is_public", "organization_guid", "source",
                             "state", "token", "timestamps", "title", "user_id"]

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

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{0} (id={1}, title={2})".format(self.__class__.__name__, self.id, self.title)

    @classmethod
    def _from_api_response(cls, api_response):
        return cls(category=api_response["category"], id=api_response["id"],
                   id_in_object_store=api_response["idInObjectStore"], is_public=api_response["publicRequest"],
                   org_guid=api_response["orgUUID"], source=api_response["source"], state=api_response["state"],
                   token=api_response["token"], timestamps=["timestamps"], title=api_response["title"],
                   user_id=api_response["userId"])

    @classmethod
    def create(cls, category="other", is_public=False, org_guid=None, source=None, title=None, user_id=0,
               client=get_admin_client()):
        if title is None:
            title = "test-transfer-{}".format(time.time())
        api_response = api.api_create_das_request(client, category=category, is_public=is_public,
                                                  org_guid=org_guid, source=source, title=title, user_id=user_id)
        return cls(category=category, id=api_response["id"], id_in_object_store=api_response["idInObjectStore"],
                   is_public=is_public, org_guid=org_guid, source=source, state=api_response["state"],
                   token=api_response["token"], timestamps=["timestamps"], title=title, user_id=user_id)

    @classmethod
    def get_list(cls, orgs, client=get_admin_client()):
        api_response = api.api_get_das_requests(client, [org.guid for org in orgs])
        transfers = []
        for transfer_data in api_response:
            transfers.append(cls._from_api_response(transfer_data))
        return transfers

    @classmethod
    def get(cls, transfer_id, client=get_admin_client()):
        api_response = api.api_get_das_request(client, transfer_id)
        return cls._from_api_response(api_response)

    def delete(self, client=get_admin_client()):
        return api.api_delete_das_request(client, self.id)
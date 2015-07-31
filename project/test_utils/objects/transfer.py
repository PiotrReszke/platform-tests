import functools
import random
import time

import test_utils.api_calls.das_api_calls as api
from test_utils import get_admin_client, get_logger


__all__ = ["Transfer"]


logger = get_logger("transfer")


@functools.total_ordering
class Transfer(object):

    TITLE_PREFIX = "transfer"

    COMPARABLE_ATTRIBUTES = ["category", "id", "is_public", "organization_guid", "source",
                             "state", "token", "timestamps", "title", "user_id"]
    new_status = "NEW"
    finished_status = "FINISHED"

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
        return "{0} (id={1}, title={2}, state={3})".format(self.__class__.__name__, self.id, self.title, self.state)

    @classmethod
    def _from_api_response(cls, api_response):
        return cls(category=api_response["category"], id=api_response["id"],
                   id_in_object_store=api_response["idInObjectStore"], is_public=api_response["publicRequest"],
                   org_guid=api_response["orgUUID"], source=api_response["source"], state=api_response["state"],
                   token=api_response["token"], timestamps=["timestamps"], title=api_response["title"],
                   user_id=api_response["userId"])

    @classmethod
    def api_create(cls, category="other", is_public=False, org_guid=None, source=None, title=None, user_id=0,
                   client=None):
        client = client or get_admin_client()
        if title is None:
            random_no = str(random.randrange(1000000)).zfill(6)
            title = cls.TITLE_PREFIX + random_no
        api_response = api.api_create_das_request(client, category=category, is_public=is_public, org_guid=org_guid,
                                                  source=source, title=title, user_id=user_id)
        return cls(category=category, id=api_response["id"], id_in_object_store=api_response["idInObjectStore"],
                   is_public=is_public, org_guid=org_guid, source=source, state=api_response["state"],
                   token=api_response["token"], timestamps=["timestamps"], title=title, user_id=user_id)

    @classmethod
    def api_get_list(cls, orgs, client=None):
        client = client or get_admin_client()
        api_response = api.api_get_das_requests(client, [org.guid for org in orgs])
        transfers = []
        for transfer_data in api_response:
            transfers.append(cls._from_api_response(transfer_data))
        return transfers

    @classmethod
    def api_get(cls, transfer_id, client=None):
        client = client or get_admin_client()
        api_response = api.api_get_das_request(client, transfer_id)
        return cls._from_api_response(api_response)

    def api_delete(self, client=None):
        client = client or get_admin_client()
        return api.api_delete_das_request(client, self.id)

    @classmethod
    def get_until_finished(cls, transfer_id, timeout=60):
        start = time.time()
        while time.time() - start < timeout:
            transfer = cls.api_get(transfer_id)
            if transfer.state == cls.finished_status:
                break
            time.sleep(20)
        return transfer

    def ensure_finished(self, timeout=120):
        transfer = self.get_until_finished(self.id, timeout)
        self.state = transfer.state
        if self.state != self.finished_status:
            raise TimeoutError("Transfer did not finished in {}s".format(timeout))


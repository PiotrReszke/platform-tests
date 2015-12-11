#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import functools
import time

from test_utils import get_logger, platform_api_calls as api, UnexpectedResponseError, get_test_name
from objects import DataSet


__all__ = ["Transfer"]


logger = get_logger("transfer")


@functools.total_ordering
class Transfer(object):

    TITLE_PREFIX = "transfer"
    COMPARABLE_ATTRIBUTES = ["category", "id", "is_public", "organization_guid", "source",
                             "state", "title", "user_id"]
    new_status = "NEW"
    finished_status = "FINISHED"

    TEST_TRANSFERS = []

    def __init__(self, category=None, id=None, id_in_object_store=None, is_public=None, org_guid=None, source=None,
                 state=None, timestamps=None, title=None, user_id=None, from_local_file=False):
        self.title, self.category, self.source = title, category, source
        self.id, self.id_in_object_store = id, id_in_object_store
        self.is_public, self.state, self.timestamps = is_public, state, timestamps
        self.organization_guid, self.user_id = org_guid, user_id
        self.from_local_file = from_local_file

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
                   timestamps=api_response["timestamps"], title=api_response["title"], user_id=api_response["userId"])

    @classmethod
    def api_create(cls, category="other", is_public=False, org=None, source=None, title=None, user_id=0,
                   client=None, from_local_file=False):
        title = get_test_name() if title is None else title
        if not from_local_file:
            response = api.api_create_transfer(category=category, is_public=is_public, org_guid=getattr(org, "guid", None),
                                               source=source, title=title, client=client)
            new_transfer = cls(category=category, id=response["id"], id_in_object_store=response["idInObjectStore"],
                           is_public=is_public, org_guid=getattr(org, "guid", None), source=source,
                           state=response["state"], timestamps=response["timestamps"], title=title, user_id=user_id)

        else:
            response = api.api_create_transfer_from_local_file(category=category, is_public=is_public,
                                                               org_guid=getattr(org, "guid", None), title=title,
                                                               client=client, file=source)
            transfer_list = cls.api_get_list(orgs=[org])
            new_transfer = next((tr for tr in transfer_list if tr.title == title), None)
        cls.TEST_TRANSFERS.append(new_transfer)
        DataSet.TEST_TRANSFER_TITLES.append(title)
        return new_transfer

    @classmethod
    def api_create_by_file_upload(cls, org, file_path, category="other", is_public=False, title=None, client=None):
        title = get_test_name() if title is None else title
        api.api_create_transfer_by_file_upload(org.guid, source=file_path, category=category, is_public=is_public,
                                               title=title, client=client)
        new_transfer = cls.api_get_transfer_by_title([org], title)
        cls.TEST_TRANSFERS.append(new_transfer)
        DataSet.TEST_TRANSFER_TITLES.append(title)
        return new_transfer

    @classmethod
    def api_get_transfer_by_title(cls, org_list, title):
        return next(iter(transfer for transfer in cls.api_get_list(org_list) if transfer.title == title))

    @classmethod
    def api_get_list(cls, org_list, client=None):
        response = api.api_get_transfers([org.guid for org in org_list], client=client)
        return [cls._from_api_response(transfer_data) for transfer_data in response]

    @classmethod
    def api_get(cls, transfer_id, client=None):
        response = api.api_get_transfer(transfer_id, client=client)
        return cls._from_api_response(response)

    @classmethod
    def get_until_finished(cls, transfer_id, timeout=60):
        start = time.time()
        while time.time() - start < timeout:
            transfer = cls.api_get(transfer_id)
            if transfer.is_finished():
                break
            time.sleep(20)
        return transfer

    def api_delete(self, client=None):
        return api.api_delete_transfer(self.id, client=client)

    def ensure_finished(self, timeout=120):
        transfer = self.get_until_finished(self.id, timeout)
        self.state = transfer.state
        self.id_in_object_store = transfer.id_in_object_store
        self.timestamps = transfer.timestamps
        if self.state != self.finished_status:
            raise AssertionError("Transfer did not finish in {}s".format(timeout))

    def is_finished(self):
        return self.finished_status in self.timestamps.keys()

    @classmethod
    def api_teardown_test_transfers(cls):
        for transfer in cls.TEST_TRANSFERS:
            try:
                transfer.api_delete()
            except UnexpectedResponseError:
                logger.warning("Failed to delete {}".format(transfer))
        cls.TEST_TRANSFERS = []

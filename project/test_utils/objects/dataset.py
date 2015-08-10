import functools

import test_utils.api_calls.data_catalog_api_calls as api
import test_utils.api_calls.hive_api_calls as hive_api
from test_utils import get_logger, get_admin_client


logger = get_logger("dataset")


@functools.total_ordering
class DataSet(object):

    COMPARABLE_ATTRIBUTES = ["category", "creationTime", "dataSample", "format", "is_public", "id",
                             "org_guid", "recordCount", "size", "source", "target_uri", "title"]

    def __init__(self, category=None, creation_time=None, data_sample=None, format=None, id=None, is_public=None,
                 org_guid=None, record_count=None, size=None, source_uri=None, target_uri=None, title=None):
        self.category = category
        self.creation_time = creation_time
        self.data_sample = data_sample
        self.format = format
        self.is_public = is_public
        self.id = id
        self.org_guid = org_guid
        self.record_count = record_count
        self.size = size
        self.source = source_uri
        self.target_uri = target_uri
        self.title = title

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.id < other.id

    def __repr__(self):
        return "{0} (title={1}, id={2})".format(self.__class__.__name__, self.title, self.id)

    @classmethod
    def _from_api_response(cls, data):
        return cls(id=data["id"], category=data["category"], title=data["title"], format=data["format"],
                   creation_time=data["creationTime"], is_public=data["isPublic"], org_guid=data["orgUUID"],
                   data_sample=data["dataSample"], record_count=data["recordCount"], size=data["size"],
                   source_uri=data["sourceUri"], target_uri=data["targetUri"])

    @classmethod
    def api_get_list(cls, org_list, query="", filters=None, size=100, time_from=0, client=None):
        return cls.api_get_list_and_metadata(org_list, query, filters, size, time_from, client)["data_sets"]

    @classmethod
    def api_get_list_and_metadata(cls, org_list, query="", filters=None, size=100, time_from=0, client=None):
        client = client or get_admin_client()
        org_guids = [org.guid for org in org_list]
        response = api.api_get_datasets(client, org_guids, query, filters, size, time_from)
        return {
            "categories": response["categories"],
            "formats": response["formats"],
            "total": response["total"],
            "data_sets": [cls._from_api_response(data) for data in response["hits"]]
        }

    @classmethod
    def api_get_matching_to_transfer(cls, org_list, transfer, client=None):
        """Find dataset which matches a transfer."""
        client = client or get_admin_client()
        datasets = DataSet.api_get_list(client=client, org_list=org_list)
        for dataset in datasets:
            if dataset.title == transfer.title:
                return dataset
        raise Exception("Transfer {} wasn't downloaded properly".format(transfer))

    @classmethod
    def api_get(cls, data_set_id, client=None):
        return cls.api_get_with_metadata(data_set_id, client)["data_set"]

    @classmethod
    def api_get_with_metadata(cls, data_set_id, client=None):
        client = client or get_admin_client()
        response = api.api_get_dataset(client, data_set_id)
        return {
            "index": response["_index"],
            "found": response["found"],
            "type": response["_type"],
            "version": response["_version"],
            "data_set": cls._from_api_response(response["_source"])
        }

    def publish_in_hive(self, client=None):
        client = client or get_admin_client()
        hive_api.api_publish_dataset(client, category=self.category, creationTime=self.creation_time,
                                     dataSample=self.data_sample, format=self.format, is_public=self.is_public,
                                     org_guid=self.org_guid, recordCount=self.record_count, size=self.size,
                                     source=self.source, target_uri=self.target_uri, title=self.title)


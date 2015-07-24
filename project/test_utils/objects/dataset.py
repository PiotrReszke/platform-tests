import test_utils.api_calls.data_catalog_api_calls as api
import test_utils.api_calls.dataset_publisher_api_calls as dataset_publisher_api
from test_utils import get_admin_client


class DataSet(object):

    def __init__(self, id, category, title, format, creation_time, is_public, org_guid, data_sample, record_count, size,
                 source_uri, target_uri):
        self.id = id
        self.category = category
        self.title = title
        self.format = format.upper()
        self.creation_time = creation_time
        self.is_public = is_public
        self.org_guid = org_guid
        self.data_sample = data_sample
        self.record_count = record_count
        self.size = size
        self.source_uri = source_uri
        self.target_uri = target_uri

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

    def api_publish_in_hive(self, client=None):
        client = client or get_admin_client()
        dataset_publisher_api.api_publish_in_hive(client, category=self.category, creation_time=self.creation_time,
                                                  data_sample=self.data_sample, format=self.format, id=self.id,
                                                  is_public=self.is_public, org_guid=self.org_guid,
                                                  record_count=self.record_count, size=self.size, title=self.title,
                                                  source_uri=self.source_uri, target_uri=self.target_uri)

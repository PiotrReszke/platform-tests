import functools
import json

from test_utils import get_admin_client
import test_utils.api_calls.service_catalog_api_calls as api
import test_utils.cli.cloud_foundry as cf


__all__ = ["ServiceType"]


@functools.total_ordering
class ServiceType(object):
    """Otherwise known as broker"""

    COMPARABLE_ATTRIBUTES = ["guid", "label", "description", "url", "tags", "space_guid", "is_active", "display_name"]

    def __init__(self, guid, label, description, url, tags, space_guid, is_active, display_name,
                 service_plan_guids=None):
        self.guid = guid
        self.label = label
        self.description = description
        self.url = url
        self.tags = tags
        self.space_guid = space_guid
        self.is_active = is_active
        self.display_name = display_name
        self.service_plan_guids = service_plan_guids

    def __repr__(self):
        return "{0} (guid={1}, label={2})".format(self.__class__.__name__, self.guid, self.label)

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.guid < other.guid

    @classmethod
    def api_get_list_from_marketplace(cls, space_guid, client=None):
        client = client or get_admin_client()
        response = api.api_get_marketplace_services(space_guid=space_guid, client=client)
        return [cls._from_details(space_guid, data) for data in response["resources"]]

    @classmethod
    def api_get(cls, space_guid, service_guid, client=None):
        client = client or get_admin_client()
        response = api.api_get_service(service_guid=service_guid, client=client)
        return cls._from_details(space_guid, response)

    @classmethod
    def _from_details(cls, space_guid, data):
        metadata = data["metadata"]
        entity = data["entity"]
        display_name = None if entity["extra"] is None else json.loads(entity["extra"]).get("displayName")
        if display_name is None:
            display_name = entity["label"]
        service_plan_guids = None
        if entity.get("service_plans") is not None:  # in cf response there are no service plans, but an url
            service_plan_guids = [sp["metadata"]["guid"] for sp in entity["service_plans"]]
        return cls(guid=metadata["guid"], label=entity["label"], description=entity["description"],
                   url=metadata["url"], tags=entity["tags"], space_guid=space_guid, is_active=entity["active"],
                   display_name=display_name, service_plan_guids=service_plan_guids)

    @classmethod
    def cf_api_get_list_from_marketplace(cls, space_guid):
        cf_response = cf.cf_api_services(space_guid)
        return [cls._from_details(space_guid, data) for data in cf_response["resources"]]


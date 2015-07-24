import functools
import json

import test_utils.cli.cloud_foundry as cf
import test_utils.api_calls.service_catalog_api_calls as api
from test_utils.objects.user import get_admin_client


__all__ = ["Marketplace"]


@functools.total_ordering
class Marketplace(object):
    COMPARABLE_ATTRIBUTES = ["space_guid", "services_count", "services_names", "tags"]

    def __init__(self, space_guid=None, services_count=0, services=None, tags=None, services_names=None):
        self.space_guid = space_guid
        self.services_count = services_count
        self.services = services
        self.tags = sorted(tags)
        self.services_names = sorted(services_names)

    def __eq__(self, other):
        return all([getattr(self, attribute) == getattr(other, attribute) for attribute in self.COMPARABLE_ATTRIBUTES])

    def __lt__(self, other):
        return self.services_count < other.services_count

    def __repr__(self):
        return "{0} (space_guid={1}, services_count={2}, services={3})".format(self.__class__.__name__, self.space_guid,
                                                                               self.services_count, self.services_names)

    @classmethod
    def api_fetch_marketplace_services(cls, space_guid=None, client=None):
        client = client or get_admin_client()
        api_response = api.api_get_marketplace_services(space_guid=space_guid, client=client)
        services = api_response["resources"]
        services_count = api_response["total_results"]
        tags = cls.get_services_tags(services)
        services_names = cls.get_services_names(services)
        return cls(space_guid=space_guid,
                   services=services, services_count=services_count,
                   tags=tags, services_names=services_names)

    @classmethod
    def cf_fetch_marketplace_services(cls, space_guid=None):
        cf_response = cf.cf_api_services(space_guid)
        services = cf_response["resources"]
        services_count = cf_response["total_results"]
        services_names = cls.get_services_names(services)
        tags = cls.get_services_tags(services)
        return cls(space_guid=space_guid,
                   services=services, services_count=services_count,
                   tags=tags, services_names=services_names)

    @classmethod
    def get_services_tags(cls, services):
        return [(service["entity"]["label"], service["entity"]["tags"]) for service in services]

    @classmethod
    def get_services_names(cls, services):
        return [service["entity"]["label"] for service in services]

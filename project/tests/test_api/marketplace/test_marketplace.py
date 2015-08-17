from test_utils.objects import ServiceType, Organization
from test_utils import ApiTestCase, get_logger


logger = get_logger("test marketplace")


class TestMarketplaceServices(ApiTestCase):

    def test_marketplace_services(self):
        seedspace_guid = Organization.get_org_and_space("seedorg", "seedspace")[1].guid
        api_marketplace = ServiceType.api_get_list_from_marketplace(seedspace_guid)
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace(seedspace_guid)
        self.assertListEqual(sorted(api_marketplace), sorted(cf_marketplace))

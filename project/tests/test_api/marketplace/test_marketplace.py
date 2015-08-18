from test_utils.objects import ServiceType
from test_utils import ApiTestCase, get_logger
from test_utils.config import get_config_value


logger = get_logger("test marketplace")


class TestMarketplaceServices(ApiTestCase):

    def test_marketplace_services(self):
        seedspace_guid = get_config_value("seedspace_guid")
        api_marketplace = ServiceType.api_get_list_from_marketplace(seedspace_guid)
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace(seedspace_guid)
        self.assertListEqual(sorted(api_marketplace), sorted(cf_marketplace))

from test_utils.objects import Marketplace
from test_utils import ApiTestCase, get_logger
from test_utils.config import get_config_value


logger = get_logger("test marketplace")


class TestMarketplaceServices(ApiTestCase):

    def test_marketplace_services(self):
        seedspace_guid = get_config_value("seedspace_guid")
        api_marketplace = Marketplace.api_fetch_marketplace_services(seedspace_guid)
        cf_marketplace = Marketplace.cf_fetch_marketplace_services(seedspace_guid)
        self.assertEqual(api_marketplace, cf_marketplace)

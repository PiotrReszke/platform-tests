from test_utils.objects import Marketplace
from test_utils.cli.cloud_foundry import cf_login
from test_utils import ApiTestCase, get_logger
from test_utils.config import get_config_value

logger = get_logger("test marketplace")


class TestMarketplaceServices(ApiTestCase):

    @classmethod
    def setUpClass(cls):
        cls.api_marketplace = Marketplace.api_fetch_marketplace_services(get_config_value("seedorg_guid")) #seedspace guid
        cf_login("seedorg", "seedspace")
        cls.cf_marketplace = Marketplace.cf_fetch_marketplace_services(get_config_value("seedorg_guid"))

    def test_marketplace_services(self):
        self.assertEqual(self.api_marketplace, self.cf_marketplace)

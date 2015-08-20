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

from test_utils.objects import ServiceType, Organization
from test_utils import ApiTestCase, get_logger


logger = get_logger("test marketplace")


class TestMarketplaceServices(ApiTestCase):

    def test_marketplace_services(self):
        seedspace_guid = Organization.get_org_and_space_by_name("seedorg", "seedspace")[1].guid
        api_marketplace = ServiceType.api_get_list_from_marketplace(seedspace_guid)
        cf_marketplace = ServiceType.cf_api_get_list_from_marketplace(seedspace_guid)
        self.assertListEqual(sorted(api_marketplace), sorted(cf_marketplace))

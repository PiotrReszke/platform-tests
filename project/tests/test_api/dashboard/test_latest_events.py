#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import unittest

from test_utils import ApiTestCase, cleanup_after_failed_setup
from objects import EventSummary, Organization, Transfer



class DashboardLatestEvents(ApiTestCase):

    TEST_TRANSFER_LINK = "http://fake-csv-server.gotapaas.eu/fake-csv/2"

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        """Regression with DPNG-2125"""
        cls.step("Create test organization")
        cls.tested_org = Organization.api_create()
        cls.step("Produce an event in the tested organization - create a data set")
        transfer = Transfer.api_create(org_guid=cls.tested_org.guid, source=cls.TEST_TRANSFER_LINK)
        transfer.ensure_finished()
        cls.step("Create another organization and create a data set in that organization")
        other_org = Organization.api_create()
        transfer = Transfer.api_create(org_guid=other_org.guid, source=cls.TEST_TRANSFER_LINK)
        transfer.ensure_finished()
        cls.step("Retrieve latest events from dashboard")
        cls.dashboard_latest_events = EventSummary.api_get_latest_events_from_org_metrics(cls.tested_org.guid)

    @unittest.expectedFailure
    def test_10_latest_events_on_dashboard_the_same_as_in_LES(self):
        """DPNG-2091 There's no organisations distinction on dashboard in latest events section"""
        self.step("Retrieve latest events from the LES filtering with tested organization")
        latest_events_response = EventSummary.api_get_latest_events(org_guid=self.tested_org.guid)
        self.step("Check that dashboard contains 10 latest events from LES")
        ten_latest_events = sorted(latest_events_response, reverse=True)[:10]
        self.assertUnorderedListEqual(ten_latest_events, self.dashboard_latest_events, "\nLatest events differ")

    @unittest.expectedFailure
    def test_latest_events_dashboard_contains_only_current_org_events(self):
        """DPNG-2091 There's no organisations distinction on dashboard in latest events section"""
        self.step("Check that dashboard contains only latest events from tested organization")
        for event in self.dashboard_latest_events:
            self.assertEqual(event.organization_id, self.tested_org.guid,
                             "Latest events on dashboard contain events from another organization")

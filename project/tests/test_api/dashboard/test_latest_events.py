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

from test_utils import ApiTestCase
from objects import EventSummary, Organization


class LatestEventsTest(ApiTestCase):

    @classmethod
    def setUpClass(cls):
        cls.seedorg, _ = Organization.get_org_and_space_by_name(org_name="seedorg")
        cls.dashboard_latest_events = EventSummary.api_get_latest_events_from_org_metrics(cls.seedorg.guid)
        cls.latest_events_response = EventSummary.api_get_latest_events()

    def test_latest_events_dashboard(self):
        latest_events = sorted(self.latest_events_response, reverse=True)[:10]
        dashboard_latest_events = sorted(self.dashboard_latest_events, reverse=True)
        self.assertCountEqual(latest_events, dashboard_latest_events, "\nLatest events differ")

    def test_latest_events_dashboard_contains_only_current_org_events(self):
        for event in self.dashboard_latest_events:
            self.assertTrue(event.organization_id == self.seedorg.guid,
                            "Latest events in dashboard contain events from other organizations")

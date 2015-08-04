from test_utils import ApiTestCase
from test_utils.objects import EventSummary


class LatestEventsTest(ApiTestCase):

    def test_latest_events(self):
        event_summary = EventSummary.api_get_latest_events()
        self.assertLessEqual(0, event_summary["total"])

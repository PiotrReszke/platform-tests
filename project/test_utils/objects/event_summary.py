import test_utils.api_calls.latest_events_service_api_calls as api
from test_utils import get_admin_client


class EventSummary(object):

    def __init__(self, total, events):
        self.total = total
        self.events = events

    @classmethod
    def api_get_latest_events(cls, client=None):
        client = client or get_admin_client()
        response = api.api_get_latest_events(client)
        return {
            "total": response["total"],
            "events": response["events"]
        }

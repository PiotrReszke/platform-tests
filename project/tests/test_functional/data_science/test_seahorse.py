import re

import pytest
import requests
import websocket
from retry import retry

from configuration import config
from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import ServiceInstance
import signal


class Seahorse(TapTestCase):
    seahorse_label = "k-seahorse-dev"
    tap_domain = config.CONFIG["domain"]
    username = config.CONFIG["admin_username"]
    password = config.CONFIG["admin_password"]

    def test_0_workflows_are_visible(self):
        workflows = self.session.get(self.seahorse_http_url + '/v1/workflows').json()
        assert len(workflows) > 5

    def test_1_workflow_can_be_cloned(self):
        workflows = self.session.get(self.workflows_url).json()
        some_workflow = list(filter(lambda w: 'Mushrooms' in w['name'], workflows))[0]

        clone_url = self.workflows_url + '/' + some_workflow["id"] + "/clone"
        clone_resp = self.session.post(clone_url, json={'name': 'Cloned workflow', 'description': 'Some desc'})
        cloned_workflow_id = clone_resp.json()['workflowId']

        self.session.get(self.workflows_url + '/' + cloned_workflow_id).json()
        return cloned_workflow_id

    def test_2_workflow_can_be_launched(self):
        workflow_id = self.clone_some_workflow_and_start_executor()

        ws = websocket.WebSocket()
        ws.connect("ws://" + self.seahorse_url + "/stomp/645/bg1ozddg/websocket")
        ws.send("""["CONNECT\nlogin:guest\npasscode:guest\naccept-version:1.1,1.0\nheart-beat:0,0\n\n\u0000"]""")
        ws.send(
            """["SUBSCRIBE\nid:sub-0\ndestination:/exchange/seahorse/seahorse.{0}.to\n\n\u0000"]""".format(workflow_id))
        ws.send("""["SUBSCRIBE\nid:sub-1\ndestination:/exchange/seahorse/workflow.{0}.{0}.to\n\n\u0000"]""".format(
            workflow_id))
        ws.send(
            '["SEND\ndestination:/exchange/seahorse/workflow.' + workflow_id + '.' + workflow_id + '.from\n\n{\\"messageType\\":\\"launch\\",\\"messageBody\\":{\\"workflowId\\":\\"' + workflow_id + '\\",\\"nodesToExecute\\":[]}}\u0000"]')

        for x in range(0, 5):
            print('Waiting for execution status for {0}. node'.format(x))
            self.ensure_node_executed_without_errors(ws)

        ws.close()
        self.session.delete(self.sessions_url + '/' + workflow_id)

    def clone_some_workflow_and_start_executor(self):
        cloned_workflow_id = self.test_1_workflow_can_be_cloned()
        self.session.post(self.sessions_url, json={'workflowId': cloned_workflow_id})
        self.ensure_executor_is_running(cloned_workflow_id)
        return cloned_workflow_id

    @retry(Exception, tries=5, delay=5)
    def ensure_node_executed_without_errors(self, ws):
        msg = self.next_message_skipping_few_heartbeats(ws)
        assert "executionStatus" in msg
        assert "FAILED" not in msg

    def next_message_skipping_few_heartbeats(self, ws):
        msg = ws.next()

        # Fixed number of heartbeats to prevent infinite loop.
        # Roughly there should be at least one non-heartbeat message for 5 hearbeats.
        number_of_heatbeats_to_skip = 5

        for x in range(0, number_of_heatbeats_to_skip):
            if "heartbeat" in msg or 'h' == msg or 'o' == msg:
                msg = ws.next()

        return msg

    @retry(AssertionError, tries=15, delay=5)
    def ensure_executor_is_running(self, workflow_id):
        sessions = list(
            filter(lambda s: s['workflowId'] == workflow_id, self.session.get(self.sessions_url).json()['sessions']))
        status = sessions[0]['status']
        assert status == 'running'

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def seahorse(cls):
        test_org_uuid = 'e06d477a-c8bb-48f0-baeb-3d709578d8af'
        test_space_uuid = 'b641e43e-b89b-4f32-b360-f1cf6bd1aa74'

        service_instance = ServiceInstance.api_create_with_plan_name(test_org_uuid, test_space_uuid,
                                                                     cls.seahorse_label,
                                                                     service_plan_name="free")

        service_instance.ensure_created()

        cls.seahorse_url = service_instance.name + '-' + service_instance.guid + "." + cls.tap_domain
        cls.seahorse_http_url = 'https://' + cls.seahorse_url
        cls.sessions_url = cls.seahorse_http_url + '/v1/sessions'
        cls.workflows_url = cls.seahorse_http_url + '/v1/workflows'

        cls.ensure_seahorse_accessible()
        login_form = cls.session.get(cls.seahorse_http_url, verify=False)
        csrf_value_regex = r"x-uaa-csrf.*value=\"(.*)\""
        match = re.search(csrf_value_regex, login_form.text, re.IGNORECASE)
        csrf_value = match.group(1)

        payload = {'username': Seahorse.username, 'password': Seahorse.password, 'X-Uaa-Csrf': csrf_value}
        cls.session.post(url='http://login.{0}/login.do'.format(Seahorse.tap_domain), data=payload)

    @classmethod
    @retry(Exception, tries=100, delay=30)
    def ensure_seahorse_accessible(cls):
        # Somehow test sometimes freezes on HTTPS connection - thats why there is timeout here
        with timeout(seconds=5):
            cls.session = requests.Session() # przeniesc
            cls.session.get(cls.seahorse_http_url, verify=False).raise_for_status()

class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)
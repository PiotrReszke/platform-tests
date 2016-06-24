from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import ServiceInstance
from configuration import config
import requests
import re
import json
import time
from retry import retry
import websocket


import websocket


class Seahorse(TapTestCase):
    seahorse_label = "k-seahorse-dev"
    tap_domain = config.CONFIG["domain"]
    username = config.CONFIG["admin_username"]
    password = config.CONFIG["admin_password"]

    def _ignore_test_workflows_are_visible(self):
        (session, seahorse_url) = self._create_session()
        workflows = session.get(seahorse_url + '/v1/workflows').json()
        assert len(workflows) > 5

    def _ignore_test_workflow_can_be_cloned(self):
        (session, seahorse_url) = self._create_session()

        workflows = session.get(seahorse_url + '/v1/workflows').json()

        first_workflow = workflows[0]

        clone_url = seahorse_url + '/v1/workflows/' + first_workflow["id"] + "/clone"
        clone_resp = session.post(clone_url, json={'name': 'Cloned workflow', 'description': 'Some desc'})
        cloned_workflow_id = clone_resp.json()['workflowId']

        session.get(seahorse_url + '/v1/workflows/' + cloned_workflow_id).json()
        return cloned_workflow_id

    def test_workflow_can_be_launched(self):
        (session, seahorse_url) = self._create_session()
        workflow_id = self.clone_some_workflow_and_start_executor()

        ws = websocket.WebSocket()
        ws.connect("ws://localhost:8080/stomp/645/bg1ozddg/websocket")
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

        session.delete(seahorse_url + '/v1/sessions/' + workflow_id)

    def clone_some_workflow_and_start_executor(self):
        (session, seahorse_url) = self._create_session()

        cloned_workflow_id = self._ignore_test_workflow_can_be_cloned()

        session_url = seahorse_url + '/v1/sessions'
        session.post(session_url, json={'workflowId': cloned_workflow_id})

        self.ensure_executor_is_running(session, seahorse_url, cloned_workflow_id)
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
        numberOfHeatbeatsToSkip = 5

        for x in range(0, numberOfHeatbeatsToSkip):
            if "heartbeat" in msg:
                msg = ws.next()

        return msg

    @retry(AssertionError, tries=15, delay=5)
    def ensure_executor_is_running(self, session, url, workflow_id):
        session_url = url + '/v1/sessions'
        sessions = list(
            filter(lambda s: s['workflowId'] == workflow_id, session.get(session_url).json()['sessions']))
        status = sessions[0]['status']
        assert status == 'running'

    def _create_session(self):
        return self._create_session_tap()
        # return self._create_session_local()

    def _create_session_tap(self):
        test_org_uuid = 'e06d477a-c8bb-48f0-baeb-3d709578d8af'
        test_space_uuid = 'b641e43e-b89b-4f32-b360-f1cf6bd1aa74'
        #
        # service_instance = ServiceInstance.api_create_with_plan_name(test_org_uuid, test_space_uuid,
        #                                                              self.seahorse_label,
        #                                                              service_plan_name="free")
        #
        # print("BEFORE SLEEP")
        # time.sleep(30)
        # print("AFTER SLEEP")

        #seahorse_url = "https://" + service_instance.name + '-' + service_instance.guid + "." + self.tap_domain
        seahorse_url = "https://test123-fc965481-39c0-4451-9269-ea5ffe1e8e64.seahorse-krb.gotapaas.eu/"
        print('Seahorse URL' + seahorse_url)

        session = requests.Session()
        print("!!!! LOGIN FORM !!!!")
        login_form = session.get(seahorse_url, verify=False)

        print('LOGIN FORM')
        print(login_form.__dict__)

        csrf_value_regex = r"x-uaa-csrf.*value=\"(.*)\""
        match = re.search(csrf_value_regex, login_form.text, re.IGNORECASE)
        csrf_value = match.group(1)
        payload = {'username': self.username, 'password': self.password, 'X-Uaa-Csrf': csrf_value}
        session.post(url='http://login.{0}/login.do'.format(self.tap_domain), data=payload)

        return (session, seahorse_url)

    def _create_session_local(self):
        return (requests.Session(), "http://localhost:8080")

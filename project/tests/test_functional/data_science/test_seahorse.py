from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import ServiceInstance
from configuration import config
import requests
import re
import json
import time
from retry import retry
import websocket

class Seahorse(TapTestCase):
    seahorse_label = "k-seahorse-dev"
    tap_domain = config.CONFIG["domain"]
    username = config.CONFIG["admin_username"]
    password = config.CONFIG["admin_password"]

    def test_workflows_are_visible(self):
        (session, seahorse_url) = self._create_session()
        workflows = session.get(seahorse_url + '/v1/workflows').json()
        assert len(workflows) > 5

    def test_workflow_can_be_cloned(self):
        (session, seahorse_url) = self._create_session()

        workflows = session.get(seahorse_url + '/v1/workflows').json()

        first_workflow = workflows[0]

        clone_url = seahorse_url + '/v1/workflows/' + first_workflow["id"] + "/clone"
        clone_resp = session.post(clone_url, json = {'name': 'Cloned workflow', 'description': 'Some desc'})
        cloned_workflow_id = clone_resp.json()['workflowId']

        session.get(seahorse_url + '/v1/workflows/' + cloned_workflow_id).json()
        return cloned_workflow_id

    def test_workflow_can_be_started(self):
        (session, seahorse_url) = self._create_session()
        
        cloned_workflow_id = self.test_workflow_can_be_cloned()

        session_url = seahorse_url + '/v1/sessions'
        post_session_resp = session.post(session_url, json = {'workflowId': cloned_workflow_id})

        self.ensure_executor_is_running(session, seahorse_url, cloned_workflow_id)

        # ws = websocket.WebSocket()
        # ws.connect("ws://example.com/websocket", http_proxy_host="proxy_host_name", http_proxy_port=3128)

    @retry(AssertionError, tries=15, delay=5)
    def ensure_executor_is_running(self, session, url, workflow_id):
        session_url = url + '/v1/sessions'
        sessions = list(
            filter(lambda s: s['workflowId'] == workflow_id, session.get(session_url).json()['sessions']))
        status = sessions[0]['status']
        assert status == 'running'

    def _create_session(self):
        return self._create_session_local()

    def _create_session_tap(self):
        # TODO return session and url from TAP
        session = requests.Session()
        login_form = session.get(instance_url, verify=False)

        print("LOGIN_FORM")
        print(login_form.text)
        print(login_form)
        csrf_value_regex = r"x-uaa-csrf.*value=\"(.*)\""
        match = re.search(csrf_value_regex, login_form.text, re.IGNORECASE)
        csrf_value = match.group(1)
        print("CSRF {0}".format(csrf_value))
        payload = {'username': login, 'password': password, 'X-Uaa-Csrf': csrf_value}
        session.post(url='http://login.{0}/login.do'.format(domain), data=payload)
        return (session, url)

    def _create_session_local(self):
        return (requests.Session(), "http://localhost:8080")
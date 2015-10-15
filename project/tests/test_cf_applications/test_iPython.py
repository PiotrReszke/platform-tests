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

import re
import unittest

from retry import retry

from test_utils import ApiTestCase, get_logger, iPython, cleanup_after_failed_setup, config
from objects import Organization, ServiceInstance, ServiceType, Application


logger = get_logger("iPython test")


class iPythonConsole(ApiTestCase):

    IPYTHON_SERVICE_LABEL = "ipython"
    TERMINAL_NO = 0
    ATK_CLIENT_INDEX = "https://pypi.analyticstoolkit.intel.com/latest/simple/"

    @property
    def terminal_no(self):
        """each test will be done in a separate terminal"""
        current_terminal = self.TERMINAL_NO
        self.TERMINAL_NO += 1
        return current_terminal

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Create test organization and test space")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Create instance of iPython service")
        cls.ipython = iPython(org_guid=cls.test_org.guid, space_guid=cls.test_space.guid)
        ipython_instance = cls.ipython.create_instance()
        cls._assert_ipython_instance_created(ipython_instance)
        cls.step("Login into iPython")
        cls.ipython.login()

    @classmethod
    @retry(AssertionError, tries=5, delay=5)
    def _assert_ipython_instance_created(cls, instance):
        cls.step("Get list of service instances and check ipython is on the list")
        instances = ServiceInstance.api_get_list(space_guid=cls.test_space.guid)
        instance = next((i for i in instances if i.name == instance.name), None)
        if instance is None:
            raise AssertionError("ipython instance is not on list")
        cls.step("Get credentials for the new ipython service instance")
        cls.ipython.get_credentials()

    @retry(AssertionError, tries=5, delay=5)
    def _assert_atk_client_is_installed(self, ipython_terminal):
        self.step("Check in terminal output that atk client was successfully installed")
        success_pattern = "Successfully installed .* trustedanalytics"
        output = ipython_terminal.get_output()
        self.assertIsNotNone(re.search(success_pattern, output[-2]))
        self.assertIn("#", output[-1])

    def _create_atk_instance(self):
        self.step("Get details of atk service")
        marketplace = ServiceType.api_get_list_from_marketplace(self.test_space.guid)
        atk_service = next(s for s in marketplace if s.label == "atk")
        self.step("Create atk instance")
        ServiceInstance.cf_api_create(space_guid=self.test_space.guid,
                                      service_plan_guid=atk_service.service_plan_guids[0],
                                      name_prefix="atk")
        self.step("Check that atk application is created and started")
        atk_app = Application.ensure_started(space_guid=self.test_space.guid, application_name_prefix="atk")
        self.atk_url = atk_app.urls[0]

    def test_iPython_terminal(self):
        self.step("Create new ipython terminal")
        terminal = self.ipython.connect_to_terminal(terminal_no=self.terminal_no)
        initial_output = terminal.get_output()
        self.assertTrue(any("#" in item for item in initial_output), "Terminal prompt missing")
        self.step("Check that Python interpreter runs OK in iPython terminal")
        terminal.send_input("python\r")  # Run Python in the terminal
        output = terminal.get_output()
        self.assertIn("Python", output[-2])
        self.assertIn(">>>", output[-1])

    def test_iPython_interactive_mode_hello_world(self):
        self.step("Create new notebook in iPython")
        notebook = self.ipython.create_notebook()
        self.step("Check that a simple command is properly handled in iPython")
        notebook.send_input("print('Hello, world!')")
        output = notebook.get_stream_result()
        self.assertEqual(output, "Hello, world!\n")

    @unittest.skip
    def test_iPython_connect_to_atk_client(self):
        """On hold until atk instance creation is possible"""
        self._create_atk_instance()
        self.step("Create new iPython terminal and install atk client")
        terminal = self.ipython.connect_to_terminal(terminal_no=self.terminal_no)
        terminal.send_input("pip2 install --extra-index-url {} trustedanalytics\r".format(self.ATK_CLIENT_INDEX))
        self._assert_atk_client_is_installed(terminal)
        self.step("Create new iPython notebook")
        notebook = self.ipython.create_notebook()
        self.step("import atk client in the notebook")
        notebook.send_input("import trustedanalytics as ta")
        self.assertEqual(notebook.check_command_status(), "ok")
        self.step("Create credentials file using atk client")
        notebook.send_input("ta.create_credentials_file('./cred_file')")
        self.assertIn("URI of the ATK server", notebook.get_prompt_text())
        notebook.send_input(self.atk_url, reply=True)
        self.assertIn("User name", notebook.get_prompt_text())
        notebook.send_input(config.CONFIG["admin_username"], reply=True)
        self.assertIn("", notebook.get_prompt_text())
        notebook.send_input(config.CONFIG["admin_password"], reply=True, obscure_from_log=True)
        self.assertEqual(notebook.check_command_status(), "ok")

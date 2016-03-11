#
# Copyright (c) 2016 Intel Corporation
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

import uuid

from constants.priority_levels import Priority
from constants.tap_components import TapComponent as TAP
from test_utils import ApiTestCase, cleanup_after_failed_setup, app_source_utils, cloud_foundry as cf
from test_utils import application_broker as broker_client, get_test_name, incremental, priority, components
from objects import Organization, Application, ServiceInstance, ServiceType
from constants.HttpStatus import HttpStatus
from test_utils.remote_logger.remote_logger_decorator import log_components


@log_components()
@components(TAP.application_broker)
class ApplicationBroker(ApiTestCase):

    @priority.medium
    def test_get_catalog(self):
        self.step("Getting catalog.")
        response = broker_client.app_broker_get_catalog()
        self.assertIsNotNone(response)

    @priority.low
    def test_cannot_delete_non_existing_service(self):
        self.step("Deleting random service.")
        guid = uuid.uuid4()
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_NOT_FOUND, "", broker_client.app_broker_delete_service,
                                            service_id=guid)


@log_components()
@incremental(Priority.medium)
@components(TAP.application_broker)
class ApplicationBrokerFlow(ApiTestCase):

    APP_REPO_PATH = "../../cf-env-demo"
    APP_COMMIT_ID = "f36c111"
    SERVICE_NAME = get_test_name(short=True)

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Clone example application repository from github")
        app_source_utils.clone_or_pull_repository("cf-env", cls.APP_REPO_PATH, owner="cloudfoundry-community")
        # checkout to older commit where app uses the same version of Ruby as installed on the TC agents
        app_source_utils.checkout_branch_pointing_to_commit(cls.APP_REPO_PATH, cls.APP_COMMIT_ID)
        cls.step("Create test organization and space")
        cls.test_org = Organization.api_create(space_names=["test-space"])
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Login to cf targeting test org and test space")
        cf.cf_login(cls.test_org.name, cls.test_space.name)
        cls.test_app = Application.push(
            space_guid=cls.test_space.guid,
            source_directory=cls.APP_REPO_PATH
        )

    @classmethod
    def tearDownClass(cls):
        if cls.cf_service is not None:
            broker_client.app_broker_delete_service(cls.cf_service.guid)
        super().tearDownClass()

    def test_0_register_service(self):
        self.step("Registering new service.")
        self.__class__.cf_service = ServiceType.app_broker_create_service_in_catalog(self.SERVICE_NAME,
                                                                                     "Example description",
                                                                                     self.test_app.guid)
        self.assertIsNotNone(self.cf_service)
        self.assertEqual(self.cf_service.label, self.SERVICE_NAME)
        response = broker_client.app_broker_get_catalog()
        services = [service['name'] for service in response["services"]]
        self.assertIn(self.SERVICE_NAME, services)

    def test_1_create_service_instance(self):
        self.step("Provisioning new service instance.")
        self.__class__.instance = ServiceInstance.app_broker_create_instance(self.test_org.guid,
                                                  self.cf_service.service_plans[0]["id"],
                                                  self.cf_service.guid,
                                                  self.test_space.guid)

    def test_2_bind_service_instance_to_app(self):
        self.step("Binding service instance to app.")
        response = broker_client.app_broker_bind_service_instance(self.instance.guid, self.test_app.guid)

        self.assertIsNotNone(response["credentials"]["url"])

    def test_3_cannot_delete_service_with_instance(self):
        self.step("Deleting service who have existing instance.")
        self.assertRaisesUnexpectedResponse(HttpStatus.CODE_INTERNAL_SERVER_ERROR, "",
                                            broker_client.app_broker_delete_service, service_id=self.cf_service.guid)
        response = broker_client.app_broker_get_catalog()
        services = [service['name'] for service in response["services"]]
        self.assertIn(self.SERVICE_NAME, services)

    def test_4_delete_service_instance(self):
        self.step("Deleting service instance.")
        broker_client.app_broker_delete_service_instance(self.instance.guid)


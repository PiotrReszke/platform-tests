#
# Copyright (c) 2015 Intel Corporation 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from datetime import datetime
import unittest

from test_utils import get_logger, ApiTestCase, app_source_utils, cleanup_after_failed_setup, cloud_foundry as cf
from objects import Organization, Application, Space


logger = get_logger("test_api_apps")


class Apps(ApiTestCase):

    APP_REPO_PATH = "../../cf-env-demo"
    APP_NAME_PREFIX = "cf_env"

    @classmethod
    def setUpClass(cls):
        cls.step("Clone example application repository from github")
        app_source_utils.clone_repository("cf-env", cls.APP_REPO_PATH, owner="cloudfoundry-community")

    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUp(self):
        self.step("Create test organization and space")
        self.test_org = Organization.api_create(space_names=["test-space"])
        self.test_space = self.test_org.spaces[0]
        self.step("Login to cf targeting test org and test space")
        cf.cf_login(self.test_org.name, self.test_space.name)
        self.test_app = self._push_app(self.test_org, self.test_space)
        self.step("Check the application is running")
        self.assertEqualWithinTimeout(120, True, self.test_app.cf_api_app_is_running)

    def _push_app(self, org, space):
        self.step("Push the example application to cf")
        name = self.APP_NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        application = Application(local_path=self.APP_REPO_PATH, name=name, space_guid=self.test_space.guid)
        application.change_name_in_manifest(name)
        application.cf_push()
        return application

    @unittest.expectedFailure
    def test_api_push_stop_start_delete(self):
        """DPNG-3037 when stopping application app name changes name to \"STOPPED\" """
        self.step("Stop the application and check that it is stopped")
        self.test_app.api_stop_app()
        self.assertEqualWithinTimeout(120, False, self.test_app.cf_api_app_is_running)
        self.step("Start the application and check that it has started")
        self.test_app.api_start_app()
        self.assertEqualWithinTimeout(120, True, self.test_app.cf_api_app_is_running)
        self.step("Delete the application and check that it doesn't exist")
        self.test_app.api_delete()
        self.assertNotInList(self.test_app, Application.cf_api_get_list(self.test_space.guid))

    def test_api_push_restage_delete(self):
        self.step("Restage the application and check that it is running")
        self.test_app.api_restage_app()
        self.assertEqualWithinTimeout(120, True, self.test_app.cf_api_app_is_running)
        self.step("Delete the application and check that it doesn't exist")
        self.test_app.api_delete()
        self.assertNotInList(self.test_app, Application.cf_api_get_list(self.test_space.guid))

    def test_delete_space_and_org_after_app_creation_and_deletion(self):
        """DPNG-2683 Cannot delete space where an app used to be"""
        self.step("Delete the test application")
        self.test_app.api_delete()
        self.step("Delete the space using platform api")
        self.test_space.api_delete()
        self.step("Check that the space is gone")
        self.assertNotInListWithRetry(self.test_space, Space.api_get_list)
        self.step("Delete the organization using platform api")
        self.test_org.api_delete()
        self.step("Check that the organization is gone")
        org_list = Organization.api_get_list()
        self.assertNotInList(self.test_org, org_list, "Organization {} has not been deleted".format(self.test_org.name))

    def test_delete_space_and_org_without_deleting_an_app(self):
        """DPNG-2694 Cannot delete space with an running app"""
        self.step("Delete the space using platform api")
        self.test_space.api_delete()
        self.step("Check that the space is gone")
        self.assertNotInListWithRetry(self.test_space, Space.api_get_list)
        self.step("Delete the test organization using platform api")
        self.test_org.api_delete()
        self.step("Check that the organization is gone")
        org_list = Organization.api_get_list()
        self.assertNotInList(self.test_org, org_list, "Organization {} has not been deleted".format(self.test_org.name))

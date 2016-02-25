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

from test_utils import ApiTestCase, app_source_utils, cleanup_after_failed_setup, cloud_foundry as cf, priority
from objects import Organization, Application, Space


class Apps(ApiTestCase):

    APP_REPO_PATH = "../../cf-env-demo"
    APP_NAME_PREFIX = "cf_env"
    APP_COMMIT_ID = "f36c111"

    @classmethod
    def setUpClass(cls):
        cls.step("Clone or Pull example application repository from github")
        app_source_utils.clone_or_pull_repository("cf-env", cls.APP_REPO_PATH, owner="cloudfoundry-community")
        # checkout to older commit where app uses the same version of Ruby as installed on the TC agents
        app_source_utils.checkout_branch_pointing_to_commit(cls.APP_REPO_PATH, cls.APP_COMMIT_ID)

    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUp(self):
        self.step("Create test organization and space")
        self.test_org = Organization.api_create(space_names=["test-space"])
        self.test_space = self.test_org.spaces[0]
        self.step("Login to cf targeting test org and test space")
        cf.cf_login(self.test_org.name, self.test_space.name)
        self.test_app = Application.push(
            space_guid=self.test_space.guid,
            source_directory=self.APP_REPO_PATH
        )
        self.step("Check the application is running")
        self.assertEqualWithinTimeout(120, True, self.test_app.cf_api_app_is_running)

    @priority.high
    def test_api_push_stop_start_restage_delete(self):
        self.step("Stop the application and check that it is stopped")
        self.test_app.api_stop()
        self.assertEqualWithinTimeout(120, False, self.test_app.cf_api_app_is_running)
        self.step("Start the application and check that it has started")
        self.test_app.api_start()
        self.assertEqualWithinTimeout(120, True, self.test_app.cf_api_app_is_running)
        self.step("Delete the application and check that it doesn't exist")
        self.test_app.api_delete()
        self.assertNotIn(self.test_app, Application.cf_api_get_list_by_space(self.test_space.guid))

    def test_delete_space_and_org_after_app_creation_and_deletion(self):
        self.step("Delete the test application")
        self.test_app.api_delete()
        self.step("Delete the space using platform api")
        self.test_space.api_delete()
        self.step("Check that the space is gone")
        self.assertNotInWithRetry(self.test_space, Space.api_get_list)
        self.step("Delete the organization using platform api")
        self.test_org.api_delete()
        self.step("Check that the organization is gone")
        self.assertNotInWithRetry(self.test_org, Organization.api_get_list)

    @priority.low
    def test_delete_space_and_org_without_deleting_an_app(self):
        self.step("Delete the space using platform api")
        self.test_space.api_delete()
        self.step("Check that the space is gone")
        self.assertNotInWithRetry(self.test_space, Space.api_get_list)
        self.step("Delete the test organization using platform api")
        self.test_org.api_delete()
        self.step("Check that the organization is gone")
        self.assertNotInWithRetry(self.test_org, Organization.api_get_list)

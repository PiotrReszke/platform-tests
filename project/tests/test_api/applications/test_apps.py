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

from test_utils import get_logger, ApiTestCase, app_source_utils, cleanup_after_failed_setup
from test_utils.objects import Organization, Application
from test_utils.cli import cloud_foundry as cf


logger = get_logger("test_api_apps")


class TestApps(ApiTestCase):

    APP_REPO_PATH = "../../cf-env-demo"
    APP_NAME_PREFIX = "cf_env"

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        app_source_utils.clone_repository("cf-env", cls.APP_REPO_PATH, owner="cloudfoundry-community")
        cls.organization = Organization.api_create(space_names=["test-space"])
        cls.space = cls.organization.spaces[0]
        cf.cf_login(cls.organization.name, cls.space.name)

    @classmethod
    def tearDownClass(cls):
        Application.delete_test_apps()
        Organization.cf_api_tear_down_test_orgs()

    def test_api_push_stop_start_delete(self):
        name = self.APP_NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        application = Application(local_path=self.APP_REPO_PATH, name=name)
        application.change_name_in_manifest(name)
        application.cf_push(self.organization, self.space)
        self.assertEqualWithinTimeout(120, True, application.cf_api_app_is_running)
        application.api_stop_app()
        self.assertEqualWithinTimeout(120, False, application.cf_api_app_is_running)
        application.api_start_app()
        self.assertEqualWithinTimeout(120, True, application.cf_api_app_is_running)
        application.api_delete()
        self.assertNotInList(application, Application.cf_api_get_list(self.space.guid))

    def test_api_push_restage_delete(self):
        name = self.APP_NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        application = Application(local_path=self.APP_REPO_PATH, name=name)
        application.change_name_in_manifest(name)
        application.cf_push(self.organization, self.space)
        self.assertEqualWithinTimeout(120, True, application.cf_api_app_is_running)
        application.api_restage_app()
        self.assertEqualWithinTimeout(120, True, application.cf_api_app_is_running)
        application.api_delete()
        self.assertNotInList(application, Application.cf_api_get_list(self.space.guid))

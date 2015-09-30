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

from test_utils import get_logger, ApiTestCase, app_source_utils, cleanup_after_failed_setup, cloud_foundry as cf
from objects import Organization, Application


logger = get_logger("test_api_apps")


class BaseTestApps(ApiTestCase):

    APP_REPO_PATH = "../../cf-env-demo"
    APP_NAME_PREFIX = "cf_env"

    @classmethod
    def tearDownClass(cls):
        Application.delete_test_apps()
        Organization.cf_api_tear_down_test_orgs()

    @classmethod
    def _push_app(cls, org, space):
        name = cls.APP_NAME_PREFIX + datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        application = Application(local_path=cls.APP_REPO_PATH, name=name)
        application.change_name_in_manifest(name)
        application.cf_push(org, space)
        return application


class TestApps(BaseTestApps):

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        app_source_utils.clone_repository("cf-env", cls.APP_REPO_PATH, owner="cloudfoundry-community")
        cls.organization = Organization.api_create(space_names=["test-space"])
        cls.space = cls.organization.spaces[0]
        cf.cf_login(cls.organization.name, cls.space.name)

    def test_api_push_stop_start_delete(self):
        application = self._push_app(self.organization, self.space)
        self.assertEqualWithinTimeout(120, True, application.cf_api_app_is_running)
        application.api_stop_app()
        self.assertEqualWithinTimeout(120, False, application.cf_api_app_is_running)
        application.api_start_app()
        self.assertEqualWithinTimeout(120, True, application.cf_api_app_is_running)
        application.api_delete()
        self.assertNotInList(application, Application.cf_api_get_list(self.space.guid))

    def test_api_push_restage_delete(self):
        application = self._push_app(self.organization, self.space)
        self.assertEqualWithinTimeout(120, True, application.cf_api_app_is_running)
        application.api_restage_app()
        self.assertEqualWithinTimeout(120, True, application.cf_api_app_is_running)
        application.api_delete()
        self.assertNotInList(application, Application.cf_api_get_list(self.space.guid))


class TestDeleteOrganizationsAfterAppCreation(BaseTestApps):

    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs, Application.delete_test_apps)
    def setUp(self):
        self.test_org = Organization.api_create(space_names=["test-space"])
        test_space = self.test_org.spaces[0]
        self.application = self._push_app(self.test_org, test_space)

    def test_delete_org_after_app_creation_and_deletion(self):
        self.assertEqualWithinTimeout(120, True, self.application.cf_api_app_is_running)
        self.application.api_delete()
        self.test_org.api_delete(with_spaces=True)
        org_list = Organization.api_get_list()
        self.assertNotInList(self.test_org, org_list, "Organization {} has not been deleted".format(self.test_org.name))

    def test_delete_org_without_deleting_an_app(self):
        self.assertEqualWithinTimeout(120, True, self.application.cf_api_app_is_running)
        self.test_org.api_delete(with_spaces=True)
        org_list = Organization.api_get_list()
        self.assertNotInList(self.test_org, org_list, "Organization {} has not been deleted".format(self.test_org.name))

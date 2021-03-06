#
# Copyright (c) 2016 Intel Corporation 
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

import pytest

from modules.constants import ServiceCatalogHttpStatus as HttpStatus, TapComponent as TAP
from modules.markers import components, priority
from modules.tap_logger import step
from modules.tap_object_model import ServiceType
from modules.test_names import generate_test_object_name
from tests.fixtures.assertions import assert_in_with_retry, assert_raises_http_exception, assert_not_in_with_retry

logged_components = (TAP.service_catalog,)
pytestmark = [components.service_catalog]


@pytest.mark.bugs("DPNG-7436 Internal Server Error (500) when trying to create a service at marketplace without a name or description")
@priority.low
def test_cannot_create_service_with_no_name(test_org, test_space, test_sample_app):
    step("Attempt to create service with empty name")
    assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                 ServiceType.register_app_in_marketplace, app_name=test_sample_app.name,
                                 app_guid=test_sample_app.guid, org_guid=test_org.guid, space_guid=test_space.guid,
                                 service_name="")


@pytest.mark.bugs("DPNG-7436 Internal Server Error (500) "
                  "when trying to create a service at marketplace without a name or description")
@priority.low
def test_cannot_create_service_with_no_description(test_org, test_space, test_sample_app):
    step("Attempt to create service with empty description")
    assert_raises_http_exception(HttpStatus.CODE_BAD_REQUEST, HttpStatus.MSG_BAD_REQUEST,
                                 ServiceType.register_app_in_marketplace, app_name=test_sample_app.name,
                                 app_guid=test_sample_app.guid, org_guid=test_org.guid, space_guid=test_space.guid,
                                 service_description="")


@priority.high
def test_create_and_delete_service(test_org, test_space, test_sample_app):
    step("Register in marketplace")
    service = ServiceType.register_app_in_marketplace(app_name=test_sample_app.name, app_guid=test_sample_app.guid,
                                                      org_guid=test_org.guid, space_guid=test_space.guid)
    step("Check that service is in marketplace")
    assert_in_with_retry(service, ServiceType.api_get_list_from_marketplace, test_space.guid)
    step("Delete service")
    service.api_delete()
    step("Check that service isn't in marketplace")
    assert_not_in_with_retry(service, ServiceType.api_get_list_from_marketplace, test_space.guid)


@priority.medium
def test_create_service_with_icon(test_org, test_space, test_sample_app, example_image):
    step("Register in marketplace")
    service = ServiceType.register_app_in_marketplace(app_name=test_sample_app.name, app_guid=test_sample_app.guid,
                                                      org_guid=test_org.guid, space_guid=test_space.guid,
                                                      image=example_image)
    step("Check that service is in marketplace")
    assert_in_with_retry(service, ServiceType.api_get_list_from_marketplace, test_space.guid)
    step("Check that images are the same")
    assert example_image == bytes(service.image, "utf8")
    step("Delete service")
    service.api_delete()


@priority.medium
def test_create_service_with_display_name(test_org, test_space, test_sample_app):
    display_name = generate_test_object_name()
    step("Register in marketplace")
    service = ServiceType.register_app_in_marketplace(app_name=test_sample_app.name, app_guid=test_sample_app.guid,
                                                      org_guid=test_org.guid, space_guid=test_space.guid,
                                                      display_name=display_name)
    step("Check that service is in marketplace")
    assert_in_with_retry(service, ServiceType.api_get_list_from_marketplace, test_space.guid)
    step("Check that display names are the same")
    assert display_name == service.display_name
    step("Delete service")
    service.api_delete()


@priority.medium
def test_create_service_with_tag(test_org, test_space, test_sample_app):
    tags = [generate_test_object_name(short=True)]
    step("Register in marketplace")
    service = ServiceType.register_app_in_marketplace(app_name=test_sample_app.name, app_guid=test_sample_app.guid,
                                                      org_guid=test_org.guid, space_guid=test_space.guid, tags=tags)
    step("Check that service is in marketplace")
    assert_in_with_retry(service, ServiceType.api_get_list_from_marketplace, test_space.guid)
    step("Check that tags names are the same")
    assert tags == service.tags
    step("Delete service")
    service.api_delete()

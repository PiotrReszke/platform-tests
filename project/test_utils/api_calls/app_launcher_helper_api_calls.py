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

from test_utils import get_logger


APP_NAME = "app-launcher-helper"
logger = get_logger("app-launcher-helper calls")


def api_get_atk_instances(client, org_guids):
    """GET /rest/orgs/{organization_guid}/atkinstances"""
    logger.info("------------------ Get atk instances for orgs {} ------------------".format(org_guids))
    return client.call(APP_NAME, "get_atk_instances", organization_guid=org_guids)

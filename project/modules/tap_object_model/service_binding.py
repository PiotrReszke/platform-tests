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

from ..http_calls import platform as api


class ServiceBinding(object):
    def __init__(self, guid, app_guid, service_instance_guid):
        self.guid = guid
        self.app_guid = app_guid
        self.service_instance_guid = service_instance_guid

    @classmethod
    def api_get_list(cls, app_guid, client=None):
        response = api.api_get_app_bindings(app_guid, client=client)
        service_bindings = []
        for instance in response:
            entity = instance["entity"]
            service_bindings.append(cls(instance["metadata"]["guid"], entity["app_guid"],
                                        entity["service_instance_guid"]))
        return service_bindings
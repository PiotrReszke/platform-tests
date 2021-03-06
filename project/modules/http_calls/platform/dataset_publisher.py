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

from ...http_client.client_auth.http_method import HttpMethod
from ...http_client.configuration_provider.console import ConsoleConfigurationProvider
from ...http_client.http_client_factory import HttpClientFactory


def api_publish_dataset(category, creation_time, data_sample, format, is_public, org_guid, record_count, size,
                        source_uri, target_uri, title, client=None):
    """POST /rest/tables"""
    body = {
        "category": category,
        "creationTime": creation_time,
        "dataSample": data_sample,
        "format": format,
        "isPublic": is_public,
        "orgUUID": org_guid,
        "recordCount": record_count,
        "size": size,
        "sourceUri": source_uri,
        "targetUri": target_uri,
        "title": title,
    }
    client = client or HttpClientFactory.get(ConsoleConfigurationProvider.get())
    return client.request(
        method=HttpMethod.POST,
        path="/rest/tables",
        body=body,
        msg="PLATFORM: publish dataset in hive"
    )

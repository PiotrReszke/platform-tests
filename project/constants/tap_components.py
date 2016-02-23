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

from enum import Enum


class TapComponent(Enum):
    auth_gateway = "auth-gateway"
    application_broker = "application-broker"
    das = "dataacquisitionservice"
    data_catalog = "datacatalog"
    hdfs_downloader = "downloader"
    hdfs_uploader = "hdfs-uploader"
    kerberos_service = "kerberos-service"
    latest_events_service = "latest-events-service"
    metadata_parser = "metadataparser"
    metrics_provider = "metrics-provider"
    service_catalog = "servicecatalog"
    service_exposer = "service-exposer"
    smtp = "smtp"
    user_management = "user-management"

    @classmethod
    def names(cls):
        return [i.name for i in list(cls)]

    @classmethod
    def values(cls):
        return [i.value for i in list(cls)]

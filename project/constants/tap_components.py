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
    app_launcher_helper = "app-launcher-helper"
    application_broker = "application-broker"
    console = "console"
    das = "dataacquisitionservice"
    data_catalog = "datacatalog"
    dataset_publisher = "datacatalogexport"
    gearpump_broker = "gearpump-broker"
    hbase_broker = "hbase-broker"
    hdfs_broker = "hdfs-broker"
    hdfs_downloader = "downloader"
    hdfs_uploader = "hdfs-uploader"
    kafka_broker = "kafka-broker"
    kerberos_service = "kerberos-service"
    latest_events_service = "latest-events-service"
    metadata_parser = "metadataparser"
    metrics_provider = "metrics-provider"
    model_catalog = "model-catalog"
    platform_context = "platformcontext"
    platform_operations = "platform-operations"
    router_metrics_provider = "router-metrics-provider"
    service_catalog = "servicecatalog"
    service_exposer = "service-exposer"
    smtp = "smtp"
    smtp_broker = "smtp-broker"
    user_management = "user-management"
    yarn_broker = "yarn-broker"
    zookeeper_broker = "zookeeper-broker"
    zookeeper_wssb_broker = "zookeeper-wssb-broker"

    ingestion_ws_kafka_hdfs = "ingestion-ws-kafka-hdfs"
    mqtt_demo = "mqtt-demo"

    atk = "atk"
    gateway = "gateway"
    scoring_engine = "scoring-engine"

    @classmethod
    def names(cls):
        return [i.name for i in list(cls)]

    @classmethod
    def values(cls):
        return [i.value for i in list(cls)]


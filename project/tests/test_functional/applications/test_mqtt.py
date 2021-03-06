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

import os
import signal
import ssl
import subprocess
import time

import paho.mqtt.client as mqtt
import pytest

from modules import app_sources
from configuration import config
from modules.constants import TapComponent as TAP, ServiceLabels, ServicePlan, TapGitHub
from modules.markers import priority, components
from modules.tap_logger import step
from modules.tap_object_model import Application, ServiceInstance
from tests.fixtures import assertions


logged_components = (TAP.mqtt_demo, TAP.service_catalog)
pytestmark = [components.mqtt_demo, components.service_catalog]


class Mqtt:

    SOURCES_OWNER = TapGitHub.intel_data
    REPO_NAME = TapGitHub.mqtt_demo
    INFLUX_INSTANCE_NAME = "mqtt-demo-db"
    MQTT_INSTANCE_NAME = "mqtt-demo-messages"
    TEST_DATA_FILE = os.path.join("fixtures", "shuttle_scale_cut_val.csv")
    SERVER_CERTIFICATE = os.path.join("fixtures", "mosquitto_demo_cert.pem")
    MQTT_TOPIC_NAME = "space-shuttle/test-data"

    @priority.medium
    @pytest.mark.skip("DPNG-7402 Push mqtt app to cf failed due to SSL error")
    def test_mqtt_demo(self, test_org, test_space, login_to_cf):
        step("Clone repository")
        mqtt_demo_sources = app_sources.AppSources(repo_name=self.REPO_NAME, repo_owner=self.SOURCES_OWNER,
                                                   gh_auth=config.CONFIG["github_auth"])
        app_repo_path = mqtt_demo_sources.clone_or_pull()
        step("Compile the sources")
        mqtt_demo_sources.compile_mvn()

        step("Create required service instances.")
        ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.INFLUX_DB,
            name=self.INFLUX_INSTANCE_NAME,
            service_plan_name=ServicePlan.FREE
        )
        ServiceInstance.api_create_with_plan_name(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.MOSQUITTO,
            name=self.MQTT_INSTANCE_NAME,
            service_plan_name=ServicePlan.FREE
        )

        step("Push mqtt app to cf")
        mqtt_demo_app = Application.push(source_directory=app_repo_path, space_guid=test_space.guid,
                                         env_proxy=config.CONFIG["pushed_app_proxy"])

        step("Retrieve credentials for mqtt service instance")
        self.credentials = mqtt_demo_app.get_credentials(service_name=ServiceLabels.MOSQUITTO)

        mqtt_port = self.credentials.get("port")
        assert mqtt_port is not None
        mqtt_username = self.credentials.get("username")
        assert mqtt_username is not None
        mqtt_pwd = self.credentials.get("password")
        assert mqtt_pwd is not None

        step("Connect to mqtt app with mqtt client")
        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(mqtt_username, mqtt_pwd)
        mqtt_client.tls_set(self.SERVER_CERTIFICATE, tls_version=ssl.PROTOCOL_TLSv1_2)
        mqtt_server_address = mqtt_demo_app.urls[0]
        mqtt_client.connect(mqtt_server_address, int(mqtt_port), 20)
        with open(self.TEST_DATA_FILE) as f:
            expected_data = f.read().split("\n")

        step("Start reading logs")
        logs = subprocess.Popen(["cf", "logs", "mqtt-demo"], stdout=subprocess.PIPE)
        time.sleep(5)

        step("Send {0} data vectors to {1}:{2} on topic {3}".format(len(expected_data), mqtt_server_address,
                                                                    mqtt_port, self.MQTT_TOPIC_NAME))
        for line in expected_data:
            mqtt_client.publish(self.MQTT_TOPIC_NAME, line)

        step("Stop reading logs. Retrieve vectors from log content.")
        grep = subprocess.Popen(["grep", "message:"], stdin=logs.stdout, stdout=subprocess.PIPE)
        logs.stdout.close()
        time.sleep(50)
        os.kill(logs.pid, signal.SIGTERM)
        cut = subprocess.Popen("cut -d ':' -f7 ", stdin=grep.stdout, stdout=subprocess.PIPE, shell=True)
        grep.stdout.close()
        step("Check that logs display all the vectors sent")
        log_result = cut.communicate()[0].decode().split("\n")
        log_result = [item.strip() for item in log_result if item not in (" ", "")]
        self.maxDiff = None  # allows for full diff to be displayed
        assert log_result == expected_data, "Data in logs do not match sent data"

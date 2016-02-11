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

import os
import signal
import ssl
import subprocess
import time
import unittest

import paho.mqtt.client as mqtt

from test_utils import ApiTestCase, get_logger, config, app_source_utils, cloud_foundry as cf, \
    cleanup_after_failed_setup
from objects import Application, Organization, ServiceType, ServiceInstance


logger = get_logger("test_mqtt")


class TestMqtt(ApiTestCase):

    INFLUX_LABEL = "influxdb088"
    INFLUX_INSTANCE_NAME = "mqtt-demo-db"
    MQTT_LABEL = "mosquitto14"
    MQTT_INSTANCE_NAME = "mqtt-demo-messages"
    APP_REPO_PATH = "../../mqtt-demo"
    TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), "shuttle_scale_cut_val.csv")
    APP_NAME = "mqtt-demo"
    MQTT_SERVER = "{}.{}".format(APP_NAME, config.CONFIG["domain"])
    SERVER_CERTIFICATE = os.path.join(os.path.dirname(__file__), "mosquitto_demo_cert.pem")
    MQTT_TOPIC_NAME = "space-shuttle/test-data"

    def _compile_mqtt_demo(self):
        self.step("Clone repository mqtt-demo")
        app_source_utils.clone_repository("mqtt-demo", self.APP_REPO_PATH)
        self.step("Compile the sources")
        app_source_utils.compile_mvn(self.APP_REPO_PATH)

    def _push_app(self, org, space):
        self.step("Login to cf")
        cf.cf_login(org.name, space.name)
        self.step("Push mqtt app to cf")
        app = Application.push(
            source_directory=self.APP_REPO_PATH,
            name=self.APP_NAME,
            space_guid=space.guid
        )
        return app

    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUp(self):
        self._compile_mqtt_demo()
        self.step("Create test organization and space")
        test_org = Organization.api_create(space_names=("test-space",))
        test_space = test_org.spaces[0]
        self.step("Create service instances of {} and {}".format(self.INFLUX_LABEL, self.MQTT_LABEL))
        ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=self.INFLUX_LABEL,
            name=self.INFLUX_INSTANCE_NAME,
            service_plan_name="free"
        )
        ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=self.MQTT_LABEL,
            name=self.MQTT_INSTANCE_NAME,
            service_plan_name="free"
        )
        mqtt_demo_app = self._push_app(test_org, test_space)
        self.step("Retrieve credentials for mqtt service instance")
        self.credentials = mqtt_demo_app.get_credentials(service_name=self.MQTT_LABEL)

    @unittest.expectedFailure
    def test_connection(self):
        """DPNG-3929 Mosquitto crendentials support"""
        mqtt_port = self.credentials.get("port")
        self.assertIsNotNone(mqtt_port)
        mqtt_username = self.credentials.get("username")
        self.assertIsNotNone(mqtt_username)
        mqtt_pwd = self.credentials.get("password")
        self.assertIsNotNone(mqtt_pwd)

        self.step("Connect to {} with mqtt client".format(self.MQTT_SERVER))
        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(mqtt_username, mqtt_pwd)
        mqtt_client.tls_set(self.SERVER_CERTIFICATE, tls_version=ssl.PROTOCOL_TLSv1_2)
        mqtt_client.connect(self.MQTT_SERVER, int(mqtt_port), 20)
        with open(self.TEST_DATA_FILE) as f:
            expected_data = f.read().split("\n")

        self.step("Start reading logs")
        logs = subprocess.Popen(["cf", "logs", "mqtt-demo"], stdout=subprocess.PIPE)
        time.sleep(5)

        self.step("Send {0} data vectors to {1}:{2} on topic {3}".format(len(expected_data), self.MQTT_SERVER,
                                                                         mqtt_port, self.MQTT_TOPIC_NAME))
        for line in expected_data:
            mqtt_client.publish(self.MQTT_TOPIC_NAME, line)

        self.step("Stop reading logs. Retrieve vectors from log content.")
        grep = subprocess.Popen(["grep", "message:"], stdin=logs.stdout, stdout=subprocess.PIPE)
        logs.stdout.close()
        time.sleep(50)
        os.kill(logs.pid, signal.SIGTERM)
        cut = subprocess.Popen("cut -d ':' -f7 ", stdin=grep.stdout, stdout=subprocess.PIPE, shell=True)
        grep.stdout.close()
        self.step("Check that logs display all the vectors sent")
        log_result = cut.communicate()[0].decode().split("\n")
        log_result = [item.strip() for item in log_result if item not in (" ", "")]
        self.maxDiff = None  # allows for full diff to be displayed
        self.assertListEqual(log_result, expected_data, "Data in logs do not match sent data")

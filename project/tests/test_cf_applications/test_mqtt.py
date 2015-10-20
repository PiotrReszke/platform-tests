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

from test_utils import ApiTestCase, get_logger, config, app_source_utils, cloud_foundry as cf
from objects import Application, Organization


logger = get_logger("test_mqtt")


class TestMqtt(ApiTestCase):

    DB_SERVICE_NAME = "influxdb088"
    DB_SERVICE_INSTANCE_NAME = "mqtt-demo-db"
    MQTT_SERVICE_NAME = "mosquitto14"
    MQTT_SERVICE_INSTANCE_NAME = "mqtt-demo-messages"
    APP_REPO_PATH = "../../mqtt-demo"
    TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), "shuttle_scale_cut_val.csv")
    APP_NAME = "mqtt-demo"
    MQTT_SERVER = "{}.{}".format(APP_NAME, config.CONFIG["domain"])
    SERVER_CERTIFICATE = os.path.join(os.path.dirname(__file__), "mosquitto_demo_cert.pem")
    MQTT_TOPIC_NAME = "space-shuttle/test-data"

    def setUp(self):
        self.step("Clone repository mqtt-demo")
        app_source_utils.clone_repository("mqtt-demo", self.APP_REPO_PATH)
        self.step("Compile the sources")
        app_source_utils.compile_mvn(self.APP_REPO_PATH)
        self.step("Login to cf")
        self.ref_org, self.ref_space = Organization.get_org_and_space_by_name(config.CONFIG["reference_org"],
                                                                              config.CONFIG["reference_space"])
        cf.cf_login(self.ref_org.name, self.ref_space.name)

    def tearDown(self):
        Application.delete_test_apps()
        cf.cf_delete_service(self.DB_SERVICE_INSTANCE_NAME)
        cf.cf_delete_service(self.MQTT_SERVICE_INSTANCE_NAME)

    def test_connection(self):
        """DPNG-2273 Error connection MQTT client"""
        self.step("Create service instances of {} and {}".format(self.DB_SERVICE_NAME, self.MQTT_SERVICE_NAME))
        cf.cf_create_service(self.DB_SERVICE_NAME, "free", self.DB_SERVICE_INSTANCE_NAME)
        cf.cf_create_service(self.MQTT_SERVICE_NAME, "free", self.MQTT_SERVICE_INSTANCE_NAME)

        self.step("Push {} application to cf".format(self.APP_NAME))
        application = Application(local_path=self.APP_REPO_PATH, name=self.APP_NAME)
        application.cf_push()
        self.step("Retrieve credentials for {} service instance".format(self.MQTT_SERVICE_NAME))
        credentials = application.cf_api_env()["VCAP_SERVICES"][self.MQTT_SERVICE_NAME][0]["credentials"]
        port_mosquitto = credentials["port"]

        self.step("Start reading logs")
        logs = subprocess.Popen(["cf", "logs", "mqtt-demo"], stdout=subprocess.PIPE)
        time.sleep(5)

        self.step("Connect to {} with an mqtt client".format(self.MQTT_SERVER))
        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(credentials["username"], credentials["password"])
        mqtt_client.tls_set(self.SERVER_CERTIFICATE, tls_version=ssl.PROTOCOL_TLSv1_2)
        mqtt_client.connect(self.MQTT_SERVER, int(port_mosquitto), 20)
        with open(self.TEST_DATA_FILE) as f:
            expected_data = f.read().split("\n")

        self.step("Send {0} data vectors to {1}:{2} on topic {3}".format(len(expected_data), self.MQTT_SERVER,
                                                                         port_mosquitto, self.MQTT_TOPIC_NAME))
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

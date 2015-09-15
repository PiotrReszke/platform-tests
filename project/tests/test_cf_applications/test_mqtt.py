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

@unittest.skip("SSL certificate error - bug DPNG-2273")
class TestMqtt(ApiTestCase):

    DB_SERVICE_NAME = "influxdb088"
    DB_SERVICE_INSTANCE_NAME = "mqtt-demo-db"
    MQTT_SERVICE_NAME = "mosquitto14"
    MQTT_SERVICE_INSTANCE_NAME = "mqtt-demo-messages"
    APP_REPO_PATH = "../../mqtt-demo"
    TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), "shuttle_scale_cut_val.csv")
    APP_NAME = "mqtt-demo"
    MQTT_SERVER = APP_NAME + '.' + config.TEST_SETTINGS["TEST_ENVIRONMENT"]
    SERVER_CERTIFICATE = os.path.join(os.path.dirname(__file__), "mosquitto_demo_cert.pem")
    MQTT_TOPIC_NAME = "space-shuttle/test-data"

    def setUp(self):
        app_source_utils.clone_repository("mqtt-demo", self.APP_REPO_PATH)
        app_source_utils.compile_mvn(self.APP_REPO_PATH)
        self.seedorg, self.seedspace = Organization.get_org_and_space_by_name("seedorg", "seedspace")
        cf.cf_login(self.seedorg.name, self.seedspace.name)

    def tearDown(self):
        Application.delete_test_apps()
        cf.cf_delete_service(self.DB_SERVICE_INSTANCE_NAME)
        cf.cf_delete_service(self.MQTT_SERVICE_INSTANCE_NAME)

    def test_connection(self):
        cf.cf_create_service(self.DB_SERVICE_NAME, "free", self.DB_SERVICE_INSTANCE_NAME)
        cf.cf_create_service(self.MQTT_SERVICE_NAME, "free", self.MQTT_SERVICE_INSTANCE_NAME)
        application = Application(local_path=self.APP_REPO_PATH, name=self.APP_NAME)
        application.cf_push(self.seedorg, self.seedspace)

        credentials = application.cf_api_env()["VCAP_SERVICES"][self.MQTT_SERVICE_NAME][0]["credentials"]
        port_mosquitto = credentials["port"]

        # start reading logs
        logs = subprocess.Popen(["cf", "logs", "mqtt-demo"], stdout=subprocess.PIPE)
        time.sleep(5)

        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(credentials["username"], credentials["password"])
        mqtt_client.tls_set(self.SERVER_CERTIFICATE, tls_version=ssl.PROTOCOL_TLSv1_2)
        mqtt_client.connect(self.MQTT_SERVER, int(port_mosquitto), 20)
        with open(self.TEST_DATA_FILE) as f:
            expected_data = f.read().split("\n")
        logger.info("Sending {0} data vectors to {1}:{2} on topic {3}...".format(len(expected_data), self.MQTT_SERVER,
                                                                                 port_mosquitto, self.MQTT_TOPIC_NAME))
        for line in expected_data:
            mqtt_client.publish(self.MQTT_TOPIC_NAME, line)
        logger.info("Done")
        connection_code = mqtt_client.disconnect()
        logger.info("Disconnected with code {}".format(connection_code))

        grep = subprocess.Popen(["grep", "message:"], stdin=logs.stdout, stdout=subprocess.PIPE)
        logs.stdout.close()
        time.sleep(50)
        os.kill(logs.pid, signal.SIGTERM)
        cut = subprocess.Popen("cut -d ':' -f7 ", stdin=grep.stdout, stdout=subprocess.PIPE, shell=True)
        grep.stdout.close()
        log_result = cut.communicate()[0].decode().split("\n")
        log_result = [item.strip() for item in log_result if item not in (" ", "")]
        self.maxDiff = None  # allows for full diff to be displayed
        self.assertListEqual(log_result, expected_data, "Data in logs do not match sent data")

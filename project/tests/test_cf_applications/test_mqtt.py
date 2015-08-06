import os
import spur
import ssl
import unittest

import paho.mqtt.client as mqtt

from test_utils import ApiTestCase, get_logger, TEST_SETTINGS
from test_utils.cli import cloud_foundry as cf
from test_utils.objects import Application, Organization, Space


logger = get_logger("test_mqtt")


@unittest.skipIf(TEST_SETTINGS["TEST_ENVIRONMENT"] == "gotapaas.eu", "Test can be run only on demo")
class TestMqtt(ApiTestCase):

    DB_SERVICE_NAME = "influxdb088"
    DB_SERVICE_INSTANCE_NAME = "mqtt-demo-db"
    MQTT_SERVICE_NAME = "mosquitto14"
    MQTT_SERVICE_INSTANCE_NAME = "mqtt-demo-messages"
    APP_REPO_PATH = "../../mqtt-demo"
    TEST_DATA_FILE = os.path.join(APP_REPO_PATH, "tools", "shuttle_scale_cut_val.csv")
    APP_NAME = "mqtt-demo"
    MQTT_SERVER = "mqtt-demo.demo-gotapaas.com"
    SERVER_CERTIFICATE = os.path.join(os.path.dirname(__file__), "mosquitto_demo_cert.pem")
    MQTT_TOPIC_NAME = "space-shuttle/test-data"

    def test_connection(self):
        org = Organization.get_seedorg()
        space = Space.get_seedspace()

        cf.cf_login(org.name, space.name)

        cf.cf_create_service(self.DB_SERVICE_NAME, "free", self.DB_SERVICE_INSTANCE_NAME)
        cf.cf_create_service(self.MQTT_SERVICE_NAME, "free", self.MQTT_SERVICE_INSTANCE_NAME)
        application = Application(local_path=self.APP_REPO_PATH, name=self.APP_NAME)
        application.cf_push(org.name, space.name)
        credentials = application.cf_env()["VCAP_SERVICES"][self.MQTT_SERVICE_NAME][0]["credentials"]
        port_mosquitto = credentials["port"]

        mqtt_client = mqtt.Client()
        mqtt_client.username_pw_set(credentials["username"], credentials["password"])
        mqtt_client.tls_set(self.SERVER_CERTIFICATE, tls_version=ssl.PROTOCOL_TLSv1_2)
        mqtt_client.connect(self.MQTT_SERVER, int(port_mosquitto), 20)
        with open(self.TEST_DATA_FILE) as f:
            data = f.readlines()
        logger.info("Sending {0} data vectors to {1}:{2} on topic {3}...".format(len(data), self.MQTT_SERVER,
                                                                                 port_mosquitto, self.MQTT_TOPIC_NAME))
        for line in data:
            mqtt_client.publish(self.MQTT_TOPIC_NAME, line)
        logger.info("Done")
        connection_code = mqtt_client.disconnect()
        logger.info("Disconnected with code {}".format(connection_code))

        try:
            shell = spur.SshShell(hostname="proxy.gotapaas.eu", username="taproot-tests", private_key_file=os.path.expanduser("~") + "/.ssh/taproot-test.dat", missing_host_key=spur.ssh.MissingHostKey.accept)
            shell.run(["true"])
        except spur.ssh.ConnectionError as error:
            print(error)


        result = shell.run(["sh", "-c", "cf logs mqtt-demo --recent | grep message: | cut -d ':' -f7"])
        log_result = str(result.output)
        log_result = log_result.replace("'","")
        log_result = log_result.replace("\\n ",'\n')[2:]
        log_result = log_result.replace("\\n","\n")


        f = open(self.TEST_DATA_FILE,"r")
        input = f.read()

        print(log_result == input)

        cf.cf_delete(self.APP_NAME)
        cf.cf_delete_service(self.DB_SERVICE_INSTANCE_NAME)
        cf.cf_delete_service(self.MQTT_SERVICE_INSTANCE_NAME)

import os
import ssl
import paho.mqtt.client as mqtt
from test_utils import ApiTestCase, get_logger, cf_login
from test_utils.cli import cloud_foundry as cf
from test_utils.objects import Application


logger = get_logger("test_mqtt")

class TestMqtt(ApiTestCase):


    def test_connection(self):
        cf_login("seedorg", "seedspace")
        cf.cf_create_service("influxdb088", "free", "mqtt-demo-db")
        cf.cf_create_service("mosquitto14", "free", "mqtt-demo-messages")
        application = Application(local_path="../../mqtt-demo", name="mqtt-demo")

        application.cf_push("seedorg", "seedspace")
        env = application.cf_env()

        a = env["VCAP_SERVICES"]["mosquitto14"][0]["credentials"]
        port_mosquitto = a['port']
        password_mosquitto = a["password"]
        username_mosquitto = a["username"]


        mqttc = mqtt.Client()
        certFile = os.path.split(__file__)[0]
        activateCert = os.path.join(certFile, 'cert.pem')

        mqttc.username_pw_set(username_mosquitto, password_mosquitto)
        mqttc.tls_set(activateCert, tls_version = ssl.PROTOCOL_TLSv1_2)
        mqttc.connect("mqtt-demo.demo-gotapaas.com", int(port_mosquitto), 20)
        with open('../../mqtt-demo/tools/shuttle_scale_cut_val.csv') as f:
            data = f.readlines()
        for line in data:
            mqttc.publish("space-shuttle/test-data", line)
        connection_code = mqttc.disconnect()
        logger.info("Disconnected with code {}".format(connection_code))

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
import json
import os
import ssl
import time
import unittest

from retry import retry
import websocket

from constants.priority_levels import Priority
from test_utils import ApiTestCase, cleanup_after_failed_setup, app_source_utils, Hdfs, config, cloud_foundry as cf, \
    incremental
from objects import Application, Organization, ServiceInstance


@incremental(Priority.medium)
class Ws2kafka2hdfs(ApiTestCase):

    MESSAGE_COUNT = 10
    APP_REPO_PATH = "../../{}/ingestion-ws-kafka-hdfs".format(config.CONFIG["repository"])
    WS2KAFKA_PATH = APP_REPO_PATH + "/ws2kafka"
    KAFKA2HDFS_PATH = APP_REPO_PATH + "/kafka2hdfs"
    KERBEROS_SERVICE = "kerberos-service"
    ENDPOINT_APP_STATS = "status/stats"
    messages = ["Test-{}".format(n) for n in range(MESSAGE_COUNT)]
    app_ws2kafka = None
    app_kafka2hdfs = None
    topic_name = None

    @retry(AssertionError, tries=5, delay=2)
    def _assert_message_count_in_app_stats(self, app, expected_message_count):
        self.step("Check that application api returns correct number of consumed messages")
        msg_count = app.api_request(path=self.ENDPOINT_APP_STATS)[0]["consumedMessages"]
        self.assertEqual(msg_count, expected_message_count,
                         "Sent {} messages, collected {}".format(expected_message_count, msg_count))

    @classmethod
    def _clone_and_compile_sources(cls):
        cls.step("Clone or Pull repository ingestion-ws-kafka-hdfs")
        app_source_utils.clone_or_pull_repository("ingestion-ws-kafka-hdfs", cls.APP_REPO_PATH)
        cls.step("Set dependency url")
        app_source_utils.set_dependency_url(cls.KAFKA2HDFS_PATH, "build.gradle")
        cls.step("Compile the sources")
        app_source_utils.compile_gradle(cls.KAFKA2HDFS_PATH)
        cls.step("Create test organization and space")

    @classmethod
    def _create_service_instances(cls, org_guid, space_guid):
        cls.step("Create instances for kafka, zookeeper, hdfs")
        ServiceInstance.api_create(
            org_guid=org_guid,
            space_guid=space_guid,
            service_label="kafka",
            name="kafka-inst",
            service_plan_name="shared"
        )
        ServiceInstance.api_create(
            org_guid=org_guid,
            space_guid=space_guid,
            service_label="zookeeper",
            name="zookeeper-inst",
            service_plan_name="shared"
        )
        ServiceInstance.api_create(
            org_guid=org_guid,
            space_guid=space_guid,
            service_label="hdfs",
            name="hdfs-inst",
            service_plan_name="shared"
        )

    @classmethod
    def _get_credentials(cls):
        cls.step("Get credentials for kerberos-service")
        user_provided_services = ServiceInstance.cf_api_get_upsi_list()
        kerb_upsi = next((upsi for upsi in user_provided_services if upsi.name == cls.KERBEROS_SERVICE), None)
        cls.assertIsNotNone(kerb_upsi, "{} not found".format(cls.KERBEROS_SERVICE))
        credentials = kerb_upsi.credentials
        return credentials

    @classmethod
    def _create_user_provided_service(cls, space_guid, credentials):
        cls.step("Create user-provided service instance for kerberos-service")
        ServiceInstance.cf_api_create_upsi(instance_name=cls.KERBEROS_SERVICE,
                                           space_guid=space_guid,
                                           credentials=credentials)

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls._clone_and_compile_sources()
        test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = test_org.spaces[0]
        cls._create_service_instances(test_org.guid, cls.test_space.guid)
        credentials = cls._get_credentials()
        cls._create_user_provided_service(cls.test_space.guid, credentials)
        cls.step("Login to cf, targeting created org and space")
        cf.cf_login(test_org.name, cls.test_space.name)
        cls.ws_opts = {"cert_reqs": ssl.CERT_NONE}
        cls.ws_protocol = "ws://"
        if config.CONFIG["ssl_validation"]:
            cls.ws_opts = {}
            cls.ws_protocol = "wss://"

    def test_step_1_push_ws2kafka2hdfs(self):
        """DPNG-5225 [hadoop-utils] remove the need for kerberos-service in non-kerberos envs"""
        postfix = str(int(time.time()))
        self.__class__.topic_name = "topic-{}".format(postfix)
        self.step("Push application ws2kafka")
        self.__class__.app_ws2kafka = Application.push(
            space_guid=self.test_space.guid,
            source_directory=self.WS2KAFKA_PATH,
            name="ws2kafka-{}".format(postfix)
        )
        self.step("Push application kafka2hdfs")
        self.__class__.app_kafka2hdfs = Application.push(
            space_guid=self.test_space.guid,
            source_directory=self.KAFKA2HDFS_PATH,
            name="kafka2hdfs-{}".format(postfix),
            bound_services= ("kafka-inst", "zookeeper-inst", "hdfs-inst",  self.KERBEROS_SERVICE,),
            env={"TOPICS": self.topic_name, "CONSUMER_GROUP": "group-{}".format(postfix)}
        )
        self.assertTrue(self.app_ws2kafka.is_started, "ws2kafka app is not started")
        self.assertTrue(self.app_kafka2hdfs.is_started, "kafka2hdfs app is not started")

    def test_step_2_send_from_ws2kafka2hdfs(self):
        connection_string = "{}/{}".format(self.app_ws2kafka.urls[0], self.topic_name)
        self._send_ws_messages(connection_string)
        self._assert_message_count_in_app_stats(self.app_kafka2hdfs, self.MESSAGE_COUNT)

    def test_step_3_check_messages_in_hdfs(self):
        """DPNG-5173 Cannot access hdfs directories using ec2-user"""
        self.step("Get details of broker guid")
        broker_guid = self.app_kafka2hdfs.get_credentials("hdfs")["uri"].split("/", 3)[3]
        self.step("Get messages from hdfs")
        hdfs_messages = self._get_messages_from_hdfs("/" + os.path.join(broker_guid, "from_kafka", self.topic_name))
        self.step("Check that all sent messages are on hdfs")
        self.assertUnorderedListEqual(hdfs_messages, self.messages)

    def _send_ws_messages(self, connection_string):
        self.step("Send messages to {}".format(connection_string))
        ws = websocket.create_connection("{}{}".format(self.ws_protocol, connection_string), sslopt=self.ws_opts)
        for message in self.messages:
            ws.send(message)

    def _get_messages_from_hdfs(self, hdfs_path):
        hdfs = Hdfs()
        topic_content = hdfs.cat(hdfs_path)
        return [m for m in topic_content.split("\n")[:-1]]


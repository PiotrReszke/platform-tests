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

import time
import ssl
import unittest
import websocket

from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup, app_source_utils, Topic, cloud_foundry \
    as cf, config
from objects import Application, Organization


logger = get_logger("cf_ws2kafka_kafka2hdfs")

class CFApp_ws2kafka_kafka2hdfs(ApiTestCase):

    MESSAGE_COUNT = 10
    APP_REPO_PATH = "../../ingestion-ws-kafka-hdfs"
    WS2KAFKA_PATH = APP_REPO_PATH + "/ws2kafka"
    KAFKA2HDFS_PATH = APP_REPO_PATH + "/kafka2hdfs"
    ENDPOINT_APP_STATS = "status/stats"
    
    @classmethod
    def tearDownClass(cls):
        Organization.cf_api_tear_down_test_orgs()

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Clone repository ingestion-ws-kafka-hdfs")
        app_source_utils.clone_repository("ingestion-ws-kafka-hdfs", cls.APP_REPO_PATH)
        cls.step("Set dependency url")
        app_source_utils.set_dependency_url(cls.KAFKA2HDFS_PATH, "build.gradle")
        cls.step("Compile the sources")
        app_source_utils.compile_gradle(cls.KAFKA2HDFS_PATH)
        cls.step("Create test organization and space")
        cls.test_org = Organization.api_create(space_names=("test-space",))
        cls.test_space = cls.test_org.spaces[0]
        cls.step("Login to cf, targeting created org and space")
        cf.cf_login(cls.test_org.name, cls.test_space.name)
        cls.step("Create instance kafka-inst service kafka")
        cf.cf_create_service("kafka", "shared", "kafka-inst")
        cls.step("Create instance zookeeper-inst service zookeeper")
        cf.cf_create_service("zookeeper", "shared", "zookeeper-inst")
        cls.step("Create instance hdfs-inst service hdfs")
        cf.cf_create_service("hdfs", "shared", "hdfs-inst")
        cls.ws_opts = {"cert_reqs": ssl.CERT_NONE}
        cls.ws_protocol = "ws://"
        if config.CONFIG["ssl_validation"]:
            cls.ws_opts = {}
            cls.ws_protocol = "wss://"

    @ApiTestCase.mark_prerequisite(is_first=True)
    def test_cf_app_step_1_push_ws2kafka_kafka2hdfs(self):
        postfix = str(int(time.time()))
        self.step("Push application ws2kafka")
        # need to assign the apps to class variables - to share with subsequent tests
        self.__class__.app_ws2kafka = self._push_ws2kafka(app_name="ws2kafka-{}".format(postfix),
                                                          topic_name="topic-{}".format(postfix))
        self.step("Push application kafka2hdfs")
        self.__class__.app_kafka2hdfs = self._push_kafka2hdfs(app_name="kafka2hdfs-{}".format(postfix),
                                                              topic_name=self.app_ws2kafka.topic,
                                                              consumer_group_name="group-{}".format(postfix))
        self.assertTrue(self.app_ws2kafka.is_started, "ws2kafka app is not started")
        self.assertTrue(self.app_kafka2hdfs.is_started, "kafka2hdfs app is not started")

    @ApiTestCase.mark_prerequisite()
    def test_cf_app_step_2_send_from_ws2kafka_to_kafka2hdfs(self):
        self.step("Send messages from ws2kafka to kafka2hdfs")
        self.expected_messages = self._send_ws_messages("{}/{}".format(self.app_ws2kafka.urls[0],
                                                                       self.app_ws2kafka.topic))
        app_stats_message_count = self._get_message_count_from_app_api(self.ENDPOINT_APP_STATS)
        self.assertEqual(app_stats_message_count, self.MESSAGE_COUNT,
                         "Sent {0} messages, collected {1}".format(self.MESSAGE_COUNT, app_stats_message_count))

    @ApiTestCase.mark_prerequisite()
    def test_cf_app_step_3_check_messages_in_hdfs(self):
        self.step("Check hdfs topic messages")
        broker_guid = self.app_kafka2hdfs.cf_api_env()["VCAP_SERVICES"]["hdfs"][0]["credentials"]["uri"].split("/")[-2]
        topic_messages = self._get_messages_from_topic(node_name="ip-10-10-10-236", broker_instance_guid=broker_guid,
                                                       topic_catalog="from_kafka", topic_name=self.app_ws2kafka.topic)
        self.assertEqual(len(topic_messages), self.MESSAGE_COUNT,
                         "Sent {0} messages, hdfs topic message count {1}".format(
                         self.MESSAGE_COUNT, len(topic_messages))
                        )
        self.assertUnorderedListEqual(topic_messages, self.expected_messages)

    @unittest.skip
    def test_cf_app_ws2kafka_gearpump_kafka2hdfs(self):
        """On hold until gearpump instance creation is possible"""
        postfix = str(int(time.time()))
        app_ws2kafka = self._push_ws2kafka(app_name="ws2kafka-gp-in", topic_name="topic-gp-in")
        app_kafka2hdfs = self._push_kafka2hdfs(app_name="kafka2hdfs-gp-out", topic_name="topic-gp-out",
                                               consumer_group_name="group-{}".format(postfix))
        expected_messages = self._send_ws_messages("{}/{}".format(app_ws2kafka.urls[0], app_ws2kafka.topic))
        app_stats_message_count = self._get_message_count_from_app_api(self.ENDPOINT_APP_STATS)
        broker_guid = app_kafka2hdfs.cf_api_env()["VCAP_SERVICES"]["hdfs"][0]["credentials"]["uri"].split("/")[-2]
        topic_messages = self._get_messages_from_topic(node_name="ip-10-10-10-236", broker_instance_guid=broker_guid,
                                                       topic_catalog="from_kafka", topic_name=app_ws2kafka.topic)
        self.assertTrue(len(topic_messages) == self.MESSAGE_COUNT and app_stats_message_count == self.MESSAGE_COUNT,
                        "hdfs topic message count: {0}, cf stats message count: {1}, should both be {2}".format(
                            len(topic_messages), app_stats_message_count, self.MESSAGE_COUNT)
                        )
        self.assertUnorderedListEqual(topic_messages, expected_messages)

    def _push_ws2kafka(self, app_name, topic_name):
        app_ws2kafka = Application(local_path=self.WS2KAFKA_PATH, name=app_name, topic=topic_name,
                                   space_guid=self.test_space.guid)
        self.step("Change name application in manifest file")
        app_ws2kafka.change_name_in_manifest(app_ws2kafka.name)
        app_ws2kafka.cf_push()
        return app_ws2kafka

    def _push_kafka2hdfs(self, app_name, topic_name, consumer_group_name):
        app_kafka2hdfs = Application(local_path=self.KAFKA2HDFS_PATH, name=app_name, space_guid=self.test_space.guid)
        self.step("Change name application in manifest file, topic and consumer group")
        app_kafka2hdfs.change_name_in_manifest(app_kafka2hdfs.name)
        app_kafka2hdfs.change_topic_in_manifest(topic_name)
        app_kafka2hdfs.change_consumer_group_in_manifest(consumer_group_name)
        app_kafka2hdfs.cf_push()
        return app_kafka2hdfs

    def _send_ws_messages(self, connection_string):
        ws = websocket.create_connection("{}{}".format(self.ws_protocol,connection_string), sslopt=self.ws_opts)
        messages = []
        for n in range(self.MESSAGE_COUNT):
            message = "Test-{}".format(n)
            ws.send(message)
            messages.append(message)
        logger.info("Send messages to {}".format(connection_string))
        return messages

    def _get_message_count_from_app_api(self, endpoint):
        cf_status_stats = self.app_kafka2hdfs.application_api_request(endpoint=endpoint)
        return cf_status_stats[0]["consumedMessages"]

    def _get_messages_from_topic(self, node_name, broker_instance_guid, topic_catalog, topic_name):
        topic = Topic(node_name=node_name, broker_instance_guid=broker_instance_guid, topic_catalog=topic_catalog,
                      topic_name=topic_name)
        return topic.get_messages()

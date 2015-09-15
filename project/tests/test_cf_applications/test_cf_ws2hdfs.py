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

import websocket

from test_utils import ApiTestCase, get_logger, app_source_utils, Topic, cloud_foundry as cf
from objects import Application, Organization


logger = get_logger("cf_ws2kafka_kafka2hdfs")


class CFApp_ws2kafka_kafka2hdfs(ApiTestCase):

    MESSAGE_COUNT = 10
    APP_REPO_PATH = "../../ingestion-ws-kafka-hdfs"
    WS2KAFKA_PATH = APP_REPO_PATH + "/ws2kafka"
    KAFKA2HDFS_PATH = APP_REPO_PATH + "/kafka2hdfs"

    @classmethod
    def tearDownClass(cls):
        Application.delete_test_apps()

    @classmethod
    def setUp(cls):
        cls.seedorg, cls.seedspace = Organization.get_org_and_space_by_name("seedorg", "seedspace")
        app_source_utils.clone_repository("ingestion-ws-kafka-hdfs", cls.APP_REPO_PATH)
        app_source_utils.compile_gradle(cls.KAFKA2HDFS_PATH)
        cf.cf_login(cls.seedorg.name, cls.seedspace.name)
        cf.cf_create_service("kafka", "shared", "kafka-inst")
        cf.cf_create_service("zookeeper", "shared", "zookeeper-inst")
        cf.cf_create_service("hdfs", "shared", "hdfs-inst")

    def test_cf_app_ws2kafka_kafka2hdfs(self):
        """Base case test for procedure ws2kafka and kafka2hdfs"""
        postfix = str(int(time.time()))
        self._push_ws2kafka(app_name="ws2kafka-{}".format(postfix), topic_name="topic-{}".format(postfix))
        self._push_kafka2hdfs(app_name="kafka2hdfs-{}".format(postfix),
                              topic_name=self.app_ws2kafka.topic,
                              consumer_group_name="group-{}".format(postfix))
        expected_messages = self._send_ws_messages("wss://" + self.app_ws2kafka.urls[0] + "/" + self.app_ws2kafka.topic)
        app_stats_message_count = self._get_message_count_from_app_api("status/stats")
        logger.info("Topic kafka {}".format(self.app_kafka2hdfs.topic))
        broker_guid = self.app_kafka2hdfs.cf_api_env()["VCAP_SERVICES"]["hdfs"][0]["credentials"]["uri"].split("/")[-2]
        topic_messages = self._get_messages_from_topic(node_name="ip-10-10-10-236", broker_instance_guid=broker_guid,
                                                       topic_catalog="from_kafka", topic_name=self.app_ws2kafka.topic)
        self.assertTrue(len(topic_messages) == self.MESSAGE_COUNT and app_stats_message_count == self.MESSAGE_COUNT,
                        "hdfs topic message count: {0}, cf stats message count: {1}, should both be {2}".format(
                            len(topic_messages), app_stats_message_count, self.MESSAGE_COUNT)
                        )
        self.assertUnorderedListEqual(topic_messages, expected_messages)

    def test_cf_app_ws2kafka_gearpump_kafka2hdfs(self):
        """Base case test for procedure ws2kafka, gearpump and kafka2hdfs"""
        postfix = str(int(time.time()))
        self._push_ws2kafka(app_name="ws2kafka-gp-in", topic_name="topic-gp-in")
        self._push_kafka2hdfs(app_name="kafka2hdfs-gp-out",
                              topic_name="topic-gp-out",
                              consumer_group_name="group-{}".format(postfix))
        expected_messages = self._send_ws_messages("wss://" + self.app_ws2kafka.urls[0] + "/" + self.app_ws2kafka.topic)
        app_stats_message_count = self._get_message_count_from_app_api("status/stats")
        broker_guid = self.app_kafka2hdfs.cf_api_env()["VCAP_SERVICES"]["hdfs"][0]["credentials"]["uri"].split("/")[-2]
        topic_messages = self._get_messages_from_topic(node_name="ip-10-10-10-236", broker_instance_guid=broker_guid,
                                                       topic_catalog="from_kafka", topic_name=self.app_ws2kafka.topic)
        self.assertTrue(len(topic_messages) == self.MESSAGE_COUNT and app_stats_message_count == self.MESSAGE_COUNT,
                        "hdfs topic message count: {0}, cf stats message count: {1}, should both be {2}".format(
                            len(topic_messages), app_stats_message_count, self.MESSAGE_COUNT)
                        )
        self.assertUnorderedListEqual(topic_messages, expected_messages)

    def _push_ws2kafka(self, app_name, topic_name):
        self.app_ws2kafka = Application(local_path=self.WS2KAFKA_PATH, name=app_name, topic=topic_name)

        self.app_ws2kafka.change_name_in_manifest(self.app_ws2kafka.name)
        self.app_ws2kafka.cf_push(self.seedorg, self.seedspace)

    def _push_kafka2hdfs(self, app_name, topic_name, consumer_group_name):
        self.app_kafka2hdfs = Application(local_path=self.KAFKA2HDFS_PATH, name=app_name)
        self.app_kafka2hdfs.change_name_in_manifest(self.app_kafka2hdfs.name)
        self.app_kafka2hdfs.change_topic_in_manifest(topic_name)
        self.app_kafka2hdfs.change_consumer_group_in_manifest(consumer_group_name)
        self.app_kafka2hdfs.cf_push(self.seedorg, self.seedspace)

    def _send_ws_messages(self, connection_string):
        ws = websocket.create_connection(connection_string)
        messages = []
        for n in range(self.MESSAGE_COUNT):
            message = "Test-{}".format(n)
            ws.send(message)
            messages.append(message)
        logger.info("Send mesages to {}".format(connection_string))
        return messages

    def _get_message_count_from_app_api(self, endpoint):
        cf_status_stats = self.app_kafka2hdfs.application_api_request(endpoint=endpoint)
        return cf_status_stats[0]["consumedMessages"]

    def _get_messages_from_topic(self, node_name, broker_instance_guid, topic_catalog, topic_name):
        topic = Topic(node_name=node_name, broker_instance_guid=broker_instance_guid, topic_catalog=topic_catalog,
                      topic_name=topic_name)
        return topic.get_messages()

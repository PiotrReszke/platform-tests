import time

import websocket

from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup
from test_utils.objects import Application
import test_utils.cli.cloud_foundry_cli as cf_cli
from test_utils.cli.hdfs import Topic


logger = get_logger("cf_ws2kafka_kafka2hdfs")


class CFApp_ws2kafka_kafka2hdfs(ApiTestCase):

    MESSAGE_COUNT = 10

    @classmethod
    def tearDownClass(cls):
        Application.delete_test_apps()

    @classmethod
    @cleanup_after_failed_setup(Application.delete_test_apps)
    def setUpClass(cls):
        cf_cli.cf_login("seedorg", "seedspace")
        cf_cli.cf_cs("kafka", "kafka-inst")
        cf_cli.cf_cs("zookeeper", "zookeeper-inst")
        cf_cli.cf_cs("hdfs", "hdfs-inst", "free")
        postfix = str(time.time())
        cls.app_ws2kafka = Application(local_path="../../ingestion-ws-kafka-hdfs/ws2kafka",
                                 name="ws2kafka-{}".format(postfix),
                                 topic="topic-{}".format(postfix))
        cls.app_ws2kafka.change_name_in_manifest(cls.app_ws2kafka.name)
        cls.app_ws2kafka.cf_push("seedorg", "seedspace")
        cls.app_kafka2hdfs = Application(local_path="../../ingestion-ws-kafka-hdfs/kafka2hdfs",
                                         name="kafka2hdfs-{}".format(postfix))
        cls.app_kafka2hdfs.change_name_in_manifest(cls.app_kafka2hdfs.name)
        cls.app_kafka2hdfs.change_topic_in_manifest(cls.app_ws2kafka.topic)
        cls.app_kafka2hdfs.change_consumer_group_in_manifest("group-{}".format(postfix))
        cls.app_kafka2hdfs.cf_push("seedorg", "seedspace")

    def test_cf_app_ws2kafka_kafka2hdfs(self):
        """Base case test for procedure ws2kafka and kafka2hdfs"""
        ws = websocket.create_connection("wss://" + self.app_ws2kafka.urls[0] + "/" + self.app_ws2kafka.topic)
        for n in range(self.MESSAGE_COUNT):
            ws.send("Test-{}".format(n))
        time.sleep(60)
        cf_status_stats = self.app_kafka2hdfs.api_get(endpoint="/status/stats", url=self.app_kafka2hdfs.urls[0])
        cf_stats_message_count = cf_status_stats[0]["consumedMessages"]
        topic = Topic(node_name="ip-10-10-10-236", broker_instance_guid=self.app_kafka2hdfs.broker_guid,
                      topic_catalog="from_kafka", topic_name=self.app_ws2kafka.topic)
        hdfs_message_count = topic.get_message_count()
        self.assertTrue(hdfs_message_count == self.MESSAGE_COUNT and cf_stats_message_count == self.MESSAGE_COUNT,
                        "hdfs topic message count: {0}, cf stats message count: {1}, should both be {2}".format(
                            hdfs_message_count, cf_stats_message_count, self.MESSAGE_COUNT)
                        )

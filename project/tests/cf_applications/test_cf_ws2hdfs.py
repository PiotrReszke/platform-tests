import time
import websocket
from test_utils import ApiTestCase, get_logger, cleanup_after_failed_setup
from test_utils import Application
import test_utils.cli.cloud_foundry_cli as cf_cli
from test_utils.cli.hdfs import Topic

logger = get_logger("cf_ws2kafka_kafka2hdfs")

class CFApp_ws2kafka_kafka2hdfs(ApiTestCase):

    COUNT_MESSAGES = 10

    @classmethod
    def tearDownClass(cls):
        Application.delete_test_app()

    @classmethod
    @cleanup_after_failed_setup(Application.delete_test_apps)
    def setUpClass(cls):
        cf_cli.cf_login("seedorg", "seedspace")
        kafka_instance = cf_cli.cf_cs("kafka", "kafka-inst")
        zookeeper_instance = cf_cli.cf_cs("zookeeper", "zookeeper-inst")
        hdfs_instance = cf_cli.cf_cs("hdfs", "hdfs-inst", "free")
        post = str(time.time())
        cls.app_ws = Application(local_path="../../ingestion-ws-kafka-hdfs/ws2kafka", name="ws2kafka-{}".format(post),
                                   topic="topic-{}".format(post))
        cls.app_ws.change_name_in_manifest(cls.app_ws.name)
        cls.app_ws.cf_push("seedorg", "seedspace")
        cls.app_kafka = Application(local_path="../../ingestion-ws-kafka-hdfs/kafka2hdfs",
                                      name="kafka2hdfs-{}".format(post))
        cls.app_kafka.change_name_in_manifest(cls.app_kafka.name)
        cls.app_kafka.change_topic_in_manifest(cls.app_ws.topic)
        cls.app_kafka.change_consumer_group_in_manifest("group-{}".format(post))
        cls.app_kafka.cf_push("seedorg", "seedspace")

    def test_cf_app_ws2kafka_kafka2hdfs(self):
        """Based case test for procedure ws2kafka and kafka2hdfs"""
        ws = websocket.create_connection("wss://" + self.app_ws.urls[0] + "/" + self.app_ws.topic)
        for n in range(self.COUNT_MESSAGES):
            ws.send("Test-{}".format(n))
        time.sleep(60)
        response = self.app_kafka.api_get(endpoint="/status/stats", url=self.app_kafka.urls[0])
        response_top = response[0]["topic"]
        response_message_count = response[0]["consumedMessages"]
        topic = Topic(node_name="ip-10-10-10-236", broker_instance_guid=self.app_kafka.broker_guid,
                      topic_catalog="from_kafka", topic_name=self.app_ws.topic)
        hdfs_count = topic.get_message_count()
        self.assertTrue(hdfs_count == self.COUNT_MESSAGES and response_message_count == self.COUNT_MESSAGES,
                        "hdfs_count = {0}, res_mess = {1}, should be {2}".format(hdfs_count, response_message_count,
                                                                                 self.COUNT_MESSAGES))

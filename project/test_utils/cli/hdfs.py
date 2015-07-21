import os
import re
import spur

from test_utils import config, get_logger
from test_utils.cli.shell_commands import log_command
from test_utils.config import get_ssh_key_passphrase


logger = get_logger("hdfs")


class Hdfs(object):

    def __init__(self, node_name, username="ec2-user"):
        test_environment = config.TEST_SETTINGS["TEST_ENVIRONMENT"]
        self.hostname = config.CONFIG[test_environment]["cdh_host"]
        self.username = username
        logger.info("Accessing HDFS on {}@{}".format(self.username, self.hostname))
        self.node_name = "hdfs://{}/".format(node_name)
        self.hadoop_fs = ["hadoop", "fs", "-fs", self.node_name]
        if test_environment == "gotapaas.eu": # due to problems with hadoop config on cdh.gotapaas.eu
            self._switch_user("hdfs")

    def _execute(self, command):
        log_command(command)
        with spur.SshShell(hostname=self.hostname, username=self.username, password=get_ssh_key_passphrase()) as shell:
            result = shell.run(command)
        if result.return_code != 0:
            raise result.to_error()
        return result

    def _switch_user(self, user):
        self._execute(["sudo", "su", "-", user])

    def ls(self, directory_path):
        """Execute ls on a directory in hdfs. Return a list of file paths."""
        command = self.hadoop_fs + ["-ls", directory_path]
        output = self._execute(command).output.decode()
        paths = []
        for line in [line for line in output.split("\n")[1:-1]]:
            r = re.search("\/.*$", line)
            paths.append(line[r.start():r.end()])
        return paths

    def cat(self, file_path):
        command = self.hadoop_fs + ["-cat", file_path]
        output = self._execute(command).output.decode()
        return output

    def test_file(self, filepath):
        command = self.hadoop_fs + ["-test", "-e", filepath]
        log_command(command)
        with spur.SshShell(hostname=self.hostname, username=self.username) as shell:
            return shell.run(command).return_code


class Topic(object):

    CF_BROKER_INSTANCES_PATH = "/cf/broker/instances"

    def __init__(self, node_name, broker_instance_guid, topic_catalog, topic_name):
        self.hdfs = Hdfs(node_name)
        self.name = topic_name
        self.path = os.path.join(self.CF_BROKER_INSTANCES_PATH, broker_instance_guid, topic_catalog, topic_name)

    def __repr__(self):
        return "{} (name={})".format(self.__class__.__name__, self.name)

    @classmethod
    def get_topics(cls, node_name, broker_instance_guid, app_name):
        hdfs = Hdfs(node_name)
        path = os.path.join(cls.CF_BROKER_INSTANCES_PATH, broker_instance_guid, app_name)
        topic_paths = hdfs.ls(path)
        topics = []
        for topic_path in topic_paths:
            topic_name = re.search("[^/]+$", topic_path).group(0)
            topics.append(cls(node_name, broker_instance_guid, app_name, topic_name))

    def exists(self):
        return self.hdfs.test_file(self.path) == 0

    def get_messages(self):
        topic_content = self.hdfs.cat(self.path)
        return [message for message in topic_content.split("\n")[:-1]]

    def get_message_count(self):
        return len(self.get_messages())


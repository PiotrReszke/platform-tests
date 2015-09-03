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
import re

from . import Hdfs


__all__ = ["Topic"]


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

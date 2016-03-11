#
# Copyright (c) 2016 Intel Corporation
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

from test_utils.config import CONFIG


class Config(object):
    # Root directory for storing remote log files
    ROOT_DIRECTORY = "{}tmp".format(os.sep)

    # Log file name format
    LOG_FILE_NAME = "{}.log"

    # How long (in seconds) to wait before make request to elastic search
    TIME_BEFORE_NEXT_CALL = 15

    # How many times we will try to get response from elastic search before give up
    NUMBER_OF_TRIALS = 5

    # Ssh tunnel configuration - local port
    ELASTIC_SSH_TUNNEL_LOCAL_PORT = 9200

    # Ssh tunnel configuration - elastic search url address
    ELASTIC_SSH_TUNNEL_URL = "http://localhost:{}/logstash-{}/_search"

    # Ssh tunnel configuration - remote username
    ELASTIC_SSH_TUNNEL_USER = "ubuntu"

    # Ssh tunnel configuration - remote host
    ELASTIC_SSH_TUNNEL_HOST = "jump.{}".format(CONFIG["domain"])

    # Ssh tunnel configuration - path to ssh key
    ELASTIC_SSH_TUNNEL_KEY_PATH = CONFIG["cdh_key_path"]

    # Elastic search host
    ELASTIC_SEARCH_HOST = "10.10.7.10"

    # Elastic search port
    ELASTIC_SEARCH_PORT = 9200

    # How long (in seconds) to wait for elastic search api to send data before giving up
    ELASTIC_SEARCH_REQUEST_TIMEOUT = 120

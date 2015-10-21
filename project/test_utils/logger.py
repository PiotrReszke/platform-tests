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

import logging
import sys

import requests

from . import config


__all__ = ["get_logger", "log_command", "log_http_request", "log_http_response"]


LOGGED_RESPONSE_BODY_LENGTH = config.CONFIG["logged_response_body_length"]


format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
logging.basicConfig(stream=sys.stdout, format=format, level=logging.DEBUG)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)
requests.packages.urllib3.disable_warnings()

def get_logger(name):
    return logging.getLogger(name)


def log_command(command, replace=None):
    logger = get_logger("shell command")
    msg = "Execute {}".format(" ".join(command))
    if replace is not None:
        msg = msg.replace(*replace)
    logger.info(msg)


def log_http_request(prepared_request, username, password=None, description=""):
    body = prepared_request.body
    if body is None:
        body = ""
    if password:
        body = body.replace(password, "[SECRET]")
    msg = [
        description,
        "----------------Request------------------",
        "Client name: {}".format(username),
        "URL: {} {}".format(prepared_request.method, prepared_request.url),
        "Headers: {}".format(prepared_request.headers),
        "Body: {}".format(body),
        "-----------------------------------------"
    ]
    get_logger("http request").debug("\n".join(msg))


def log_http_response(response, logged_body_length=LOGGED_RESPONSE_BODY_LENGTH):
    """If logged_body_length < 0, full response body is logged"""
    body = response.text
    if logged_body_length == 0:
        body = "[...]"
    elif len(body) > logged_body_length > 0:
        half = logged_body_length // 2
        body = "{} [...] {}".format(body[:half], body[-half:])
    msg = [
        "\n----------------Response------------------",
        "Status code: {}".format(response.status_code),
        "Headers: {}".format(response.headers),
        "Content: {}".format(body),
        "-----------------------------------------\n"
    ]
    get_logger("http response").debug("\n".join(msg))

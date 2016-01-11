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
import json
import sys
import os

import requests

from datetime import datetime
from teamcity import is_running_under_teamcity


__all__ = ["get_logger", "set_level", "log_command", "log_http_request", "log_http_response",
           "LOGGED_RESPONSE_BODY_LENGTH", "change_log_file_path"]


__LOGGING_LEVEL = logging.NOTSET
LOGGED_RESPONSE_BODY_LENGTH = 0


requests.packages.urllib3.disable_warnings()
logger_format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
if is_running_under_teamcity():
    logging.basicConfig(stream=sys.stdout, format=logger_format)
else:
    log_file_name = "api_tests_log_{}.txt".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
    default_log_dir = os.path.join("/tmp", log_file_name)
    fh = logging.FileHandler(default_log_dir)
    sh = logging.StreamHandler(sys.stdout)
    logging.basicConfig(format=logger_format, handlers=[sh, fh])


def change_log_file_path(log_file_dir):
    logger = logging.getLogger()
    log_dir = os.path.join(log_file_dir, log_file_name)
    if fh in logger.handlers:
        fh.close()  # close opened log file
        logger.removeHandler(fh)
        try:
            os.rename(default_log_dir, log_dir)  # try to move created log file to new directory
        except OSError:
            logger.exception("Can't move log file '{}' to '{}'.".format(default_log_dir, log_dir))
    new_file_handler = logging.FileHandler(log_dir)
    new_file_handler.setFormatter(logging.Formatter(logger_format))
    logger.addHandler(new_file_handler)


def set_level(level_name):
    global __LOGGING_LEVEL
    __LOGGING_LEVEL = getattr(logging, level_name)
    # set logging level to all already-defined loggers
    for _, logger in logging.Logger.manager.loggerDict.items():
        if not isinstance(logger, logging.PlaceHolder):
            logger.setLevel(__LOGGING_LEVEL)
    # set custom logging levels to third-party library loggers
    logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(__LOGGING_LEVEL)
    logging.getLogger("paramiko.transport").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(__LOGGING_LEVEL)
    return logger


def log_command(command, replace=None):
    logger = get_logger("shell command")
    msg = "Execute {}".format(" ".join(command))
    if replace is not None:
        msg = msg.replace(*replace)
    logger.info(msg)


def log_http_request(prepared_request, username, password=None, description="", data=None):
    body = prepared_request.body if not data else json.dumps(data)
    if body is None:
        body = ""
    if password:
        body = str(body).replace(password, "[SECRET]")
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


def log_http_response(response, logged_body_length=None):
    """If logged_body_length < 0, full response body is logged"""
    if logged_body_length is None:
        logged_body_length = LOGGED_RESPONSE_BODY_LENGTH
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

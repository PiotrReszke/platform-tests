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
from multiprocessing import Queue
from enum import Enum

from test_utils import get_logger, SshTunnel
from constants.LoggerType import LoggerType
from .config import Config
from .log_provider import LogProvider
from .log_provider_configuration import LogProviderConfiguration
from .remote_logger_configuration import RemoteLoggerConfiguration

logger = get_logger(LoggerType.REMOTE_LOGGER)


class RemoteLogger(object):
    """Object for getting logs from remote sources."""

    def __init__(self, configuration: RemoteLoggerConfiguration):
        self.__configuration = configuration
        self.__ssh_tunnel = SshTunnel(
            hostname=Config.ELASTIC_SEARCH_HOST,
            port=Config.ELASTIC_SEARCH_PORT,
            username=Config.ELASTIC_SSH_TUNNEL_USER,
            path_to_key=Config.ELASTIC_SSH_TUNNEL_KEY_PATH,
            via_hostname=Config.ELASTIC_SSH_TUNNEL_HOST,
            local_port=Config.ELASTIC_SEARCH_PORT
        )

    def log_to_file(self):
        """Read remote logs and write them to file."""
        try:
            logger.info("Open ssh tunnel")
            self.__ssh_tunnel.connect()
            logs = self.__get_logs()
            self.__save_logs(logs)
        finally:
            logger.info("Close ssh tunnel")
            self.__ssh_tunnel.disconnect()

    def __get_logs(self):
        """Run multiple log providers, one for each application.
        Wait for each process to finish and then collect all logs that have been read."""
        queue = Queue()
        processes = []
        logs = {}
        logger.info("Start collecting remote logs")
        for app_name in self.__configuration.app_names:
            log_provider_configuration = self.__create_log_provider_configuration(app_name)
            process = LogProvider(log_provider_configuration, queue)
            processes.append(process)
            process.start()
        for i in range(len(self.__configuration.app_names)):
            logs.update(queue.get())
        for p in processes:
            p.join()
        return logs

    def __create_log_provider_configuration(self, app_name: Enum):
        """Create log provider configuration."""
        return LogProviderConfiguration(
            from_date=self.__configuration.from_date,
            to_date=self.__configuration.to_date,
            app_name=app_name.value
        )

    def __save_logs(self, logs):
        """Write logs to files, one separate file for each application name."""
        dir_path = os.path.join(Config.ROOT_DIRECTORY, self.__configuration.destination_directory)
        os.makedirs(dir_path, exist_ok=True)
        for app_name, app_log in logs.items():
            if app_log != LogProvider.EMPTY_LOG:
                self.__save_log(app_name, app_log, dir_path)
            else:
                logger.error("Empty log has been returned for: {}".format(app_name))

    @staticmethod
    def __save_log(app_name, app_log, dir_path):
        """Write log to file."""
        file_name = Config.LOG_FILE_NAME.format(app_name)
        file_path = os.path.join(dir_path, file_name)
        logger.info("Save log to file: {}".format(file_path))
        with open(file_path, 'w') as file:
            file.write(app_log)

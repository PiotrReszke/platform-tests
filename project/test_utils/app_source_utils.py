#
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import shutil
import subprocess

from git import Repo

from . import config, log_command, get_logger


logger = get_logger("source utils")


def clone_repository(repository_name, target_directory, owner="intel-data"):
    API_URL = "https://{2}:{3}@github.com/{0}/{1}.git".format(owner, repository_name, *config.CONFIG["github_auth"])
    logger.info("Clone from {} to {}".format(API_URL, target_directory))
    if os.path.exists(target_directory):
        shutil.rmtree(target_directory)
    os.mkdir(target_directory)
    Repo.clone_from(API_URL, target_directory)


def compile_mvn(directory):
    logger.info("Compile maven project {}".format(directory))
    current_path = os.getcwd()
    os.chdir(directory)
    command = ["mvn", "clean", "package"]
    log_command(command)
    subprocess.call(command)
    os.chdir(current_path)
    logger.info("Compiled maven project {}".format(directory))


def compile_gradle(directory):
     logger.info("Compile gradle project {}".format(directory))
     current_path = os.getcwd()
     os.chdir(directory)
     command = ["./gradlew", "assemble"]
     log_command(command)
     subprocess.call(command)
     os.chdir(current_path)
     logger.info("Compiled gradle project {}".format(directory))

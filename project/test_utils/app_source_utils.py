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
import shutil
import subprocess

from git import Repo
from test_utils import config


def clone_repository(repository_name, target_directory, owner="intel-data"):
    API_URL = "https://{}:{}@github.com/{}/{}.git".format(config.get_github_username(), config.get_github_password(), owner, repository_name)
    if os.path.exists(target_directory):
        shutil.rmtree(target_directory)
    os.mkdir(target_directory)
    Repo.clone_from(API_URL, target_directory)


def compile_mvn(directory):
    current_path = os.getcwd()
    os.chdir(directory)
    subprocess.call(["mvn", "clean", "package"])
    os.chdir(current_path)
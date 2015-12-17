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

import base64
import json
import os
import re
import shutil
import subprocess

from git import Repo
import requests

from . import config, log_command, get_logger, log_http_request, log_http_response


logger = get_logger(__name__)

# Build gradle has problem with dependency and artifact
url = "\"http://nexus.sclab.intel.com:8080/content/groups/public\""


def github_get_file_content(repository, file_path, owner="intel-data", ref=None):
    url = "https://api.github.com/repos/{}/{}/contents/{}".format(owner, repository, file_path)
    session = requests.session()
    request = session.prepare_request(requests.Request(method="GET", url=url, params={"ref": ref},
                                                       auth=config.CONFIG["github_auth"]))
    log_http_request(request, "")
    response = session.send(request)
    log_http_response(response)
    if response.status_code != 200:
        raise Exception("Github API response is {} {}".format(response.status_code, response.text))
    encoding = response.encoding
    response_content = response.content.decode(encoding)
    return base64.b64decode(json.loads(response_content)["content"])


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


def set_dependency_url(application_path, filename):
    """Set url with dependency to can build deplayable jar"""
    file_path = os.path.join(application_path, filename)
    with open(file_path, "r") as f:
        file_content = f.read()
    str = "maven {url " + url + "}"
    nodes = re.findall(r'repositories \{([^}]+)\}', file_content)
    repositories_node = file_content.find(nodes[1])
    ins_str = repositories_node + len(nodes[1])
    file_content = file_content[:ins_str] + str + file_content[ins_str:]
    with open(file_path, "w") as f:
        f.write(file_content)


def checkout_branch_pointing_to_commit(repo_path, commit_id):
    """Create branch which points to chosen commit and switch to it"""
    repo = Repo(repo_path)
    branch_name = "branch_{}".format(commit_id)
    logger.info("Create branch {} and switch to it".format(branch_name))
    repo.git.checkout(commit_id, b=branch_name)

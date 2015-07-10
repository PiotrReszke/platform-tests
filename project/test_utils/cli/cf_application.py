import base64
import json
import os
import re

import requests
import yaml

import test_utils.cli.cloud_foundry_cli as cf_cli
import test_utils.cli.shell_commands as shell_commands
from test_utils import get_logger, config


logger = get_logger("cf_application")


def github_get_file_content(repository, path, owner="intel-data"):
    endpoint = "https://api.github.com/repos/{}/{}/contents/{}".format(owner, repository, path)
    logger.info("Retrieving content of {}/{}/{}".format(owner, repository, path))
    auth = config.TEST_SETTINGS["GITHUB_AUTH"]
    response = requests.get(endpoint, auth=auth)
    if response.status_code != 200:
        raise Exception("Github API response is {}".format(response.status_code))
    encoding = response.encoding
    response_content = response.content.decode(encoding)
    return base64.b64decode(json.loads(response_content)["content"])


class CfApplication(object):

    MANIFEST_NAME = "manifest.yml"

    def __init__(self, local_path=None, name=None, state=None, instances=None, memory=None, disk=None, *urls):
        """local_path - directory where application manifest is located"""
        self.name = name
        self.state = state
        self.instances = instances
        self.memory = memory
        self.disk = disk
        self.urls = urls
        self.local_path = local_path
        self.manifest_path = os.path.join(local_path, self.MANIFEST_NAME)
        with open(self.manifest_path) as f:
            self.manifest = yaml.load(f.read())

    def __repr__(self):
        return "{0} (name={1})".format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return (self.name == other.name and self.state == other.state and self.instances == other.instances and
                self.memory == other.memory and self.disk == other.disk and self.urls == other.urls)

    def __save_manifest(self):
        with open(self.manifest_path, "w") as f:
            f.write(yaml.dump(self.manifest))

    @classmethod
    def get_list_from_settings(cls, settings_yml, state="started"):
        applications = []
        settings = yaml.load(settings_yml)
        for app_info in settings["applications"] + settings["user_provided_service_instances"] + settings["service_brokers"]:
            applications.append(cls(name=app_info["name"], state=state))
        return applications

    @classmethod
    def cf_get_list(cls):
        """Get list of applications from Cloud Foundry"""
        applications = []
        output = cf_cli.cf_apps()
        for line in output.split("\n")[4:-1]:
            data = [item for item in re.split("\s|,", line) if item != ""]
            applications.append(cls(*data))
        return applications

    def cf_push(self, organization, space):
        cf_cli.cf_target(organization, space)
        shell_commands.cd(self.local_path)
        cf_cli.cf_push()

    def change_name_in_manifest(self, new_name):
        self.manifest["applications"]["name"] = new_name
        self.__save_manifest()

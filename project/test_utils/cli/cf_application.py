import base64
import json
import os
import re
import subprocess

import requests
import yaml

import test_utils.cli.cloud_foundry_cli as cf_cli
import test_utils.cli.shell_commands as shell
from test_utils import get_logger, config

logger = get_logger("cf_application")

def __log_command(command, replace=()):
    logger.info("Execute {}".format(" ".join(command)).replace(replace))


def github_get_file_content(repository, path, owner="intel-data"):
    endpoint = "https://api.github.com/repos/{}/{}/contents/{}".format(owner, repository, path)
    logger.info("Retrieving content of {}/{}/{}".format(owner, repository, path))
    auth = config.TEST_SETTINGS["GITHUB_AUTH"]
    response = requests.get(endpoint, auth=auth)
    logger.info("Response {}".format(response))
    if response.status_code != 200:
        raise Exception("Github API response is {}".format(response.status_code))
    encoding = response.encoding
    response_content = response.content.decode(encoding)
    return base64.b64decode(json.loads(response_content)["content"])

def status_stats(urls):
    endpoint = "http://" + urls + "/status/stats"
    response = requests.get(endpoint)
    logger.info("Response {}".format(response))
    if response.status_code != 200:
        raise Exception("Status stats response is {}".format(response.status_code))
    return json.loads(response.text)

class CfApplication(object):

    MANIFEST_NAME = "manifest.yml"
    TEST_APP = []

    def __init__(self, local_path=None, name=None, state=None, instances=None, memory=None, disk=None, org_name=None,
                 space_name=None, urls=None, topic=None):
        """local_path - directory where application manifest is located"""
        self.name = name
        self.state = state
        self.instances = instances
        self.memory = memory
        self.disk = disk
        self.urls = urls
        self.org_name = org_name
        self.space_name = space_name
        self.local_path = local_path
        self.topic = topic
        self.manifest_path = str(os.path.join(local_path, self.MANIFEST_NAME))
        with open(self.manifest_path) as f:
            self.manifest = yaml.load(f.read())
        self.local_jar = self.local_path
        if "path" in self.manifest["applications"][0]:
            self.local_jar = self.local_jar + "/" + self.manifest["applications"][0]["path"]

    def __repr__(self):
        return "{0} (name={1})".format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return (self.name == other.name and self.state == other.state and self.instances == other.instances and
                self.memory == other.memory and self.disk == other.disk and self.urls == other.urls)

    def __save_manifest(self):
        with open(self.manifest_path, "w") as f:
            f.write(yaml.dump(self.manifest))

    @classmethod
    def delete_test_app(cls):
        while len(cls.TEST_APP) > 0:
            app = cls.TEST_APP[0]
            app.delete()

    def delete(self):
        self.TEST_APP.remove(self)
        return cf_cli.delete_application(self.name)

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
        output = cf_cli.cf_push(self.local_path, self.local_jar)
        self.TEST_APP.append(self)
        for line in output.split("\n"):
            if line[0:5] == "urls:":
                self.urls = re.split(r'urls: ', line)[1]

    def change_name_in_manifest(self, new_name):
        self.manifest["applications"][0]["name"] = new_name
        self.__save_manifest()

    def change_topic_in_manifest(self, new_topic):
        self.manifest["applications"][0]["env"]["TOPICS"] = new_topic
        self.__save_manifest()

    def change_consumer_group_in_manifest(self, new_consumer_group):
        self.manifest["applications"][0]["env"]["CONSUMER_GROUP"] = new_consumer_group
        self.__save_manifest()

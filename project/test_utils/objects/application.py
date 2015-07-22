import base64
import json
import os
import re
import collections

import requests
import yaml

import test_utils.cli.cloud_foundry as cf
from test_utils.api_calls import service_catalog_api_calls as api
from test_utils.logger import get_logger
from test_utils import config


logger = get_logger("application")


__all__ = ["Application", "github_get_file_content"]



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

class Application(object):

    MANIFEST_NAME = "manifest.yml"
    TEST_APPS = []

    def __init__(self, local_path=None, name=None, state=None, instances=None, memory=None, disk=None, org_name=None,
                 space_name=None, urls=(), topic=None, guid=None):
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
        self.guid = guid
        self.local_path = local_path
        self.local_jar = self.local_path
        if self.local_path is not None:
            self.manifest_path = str(os.path.join(local_path, self.MANIFEST_NAME))
            with open(self.manifest_path) as f:
                self.manifest = yaml.load(f.read())
            if "path" in self.manifest["applications"][0]:
                self.local_jar = self.local_jar + "/" + self.manifest["applications"][0]["path"]
        self._broker_guid = None

    @property
    def broker_guid(self):
        if self._broker_guid is None:
            cf_env = self.cf_env()
            self._broker_guid = cf_env["VCAP_SERVICES"]["hdfs"][0]["credentials"]["uri"].split("/")[-2]
        return self._broker_guid

    def __repr__(self):
        return "{0} (name={1})".format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return (self.name == other.name and self.state == other.state and self.instances == other.instances and
                self.memory == other.memory and self.disk == other.disk and self.urls == other.urls)

    def __save_manifest(self):
        with open(self.manifest_path, "w") as f:
            f.write(yaml.dump(self.manifest))

    @classmethod
    def delete_test_apps(cls):
        while len(cls.TEST_APPS) > 0:
            app = cls.TEST_APPS[0]
            app.delete()

    def delete(self):
        self.TEST_APPS.remove(self)
        return cf.cf_delete(self.name)

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
        output = cf.cf_apps()
        for line in output.split("\n")[4:-1]:
            data = [item for item in re.split("\s|,", line) if item != ""]
            applications.append(cls(name=data[0], state=data[1], instances=data[2], memory=data[3], disk=data[4],
                                    urls=data[5:]))
        return applications

    def api_get(self, endpoint, url=None):
        url = url or self.urls[0]
        url = "http://" + url + endpoint
        logger.info("------------------------------------------ GET {} ------------------------------------------".format(url))
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Response code is {}".format(response.status_code))
        return json.loads(response.text)

    def cf_push(self, organization, space):
        cf.cf_target(organization, space)
        output = cf.cf_push(self.local_path, self.local_jar)
        self.TEST_APPS.append(self)
        for line in output.split("\n"):
            if line[0:5] == "urls:":
                self.urls = (re.split(r'urls: ', line)[1],)

    def cf_env(self):
        output = cf.cf_env(self.name)
        start = re.search("^\{$", output, re.MULTILINE).start()
        end = re.search("^\}$", output, re.MULTILINE).end()
        return json.loads(output[start:end])

    def change_name_in_manifest(self, new_name):
        self.manifest["applications"][0]["name"] = new_name
        self.__save_manifest()

    def change_topic_in_manifest(self, new_topic):
        self.manifest["applications"][0]["env"]["TOPICS"] = new_topic
        self.__save_manifest()

    def change_consumer_group_in_manifest(self, new_consumer_group):
        self.manifest["applications"][0]["env"]["CONSUMER_GROUP"] = new_consumer_group

    @classmethod
    def cf_get_app_summary(cls, app_guid):
        path = "/v2/apps/" + app_guid + "/summary"
        return json.loads(cf.cf_curl(path, 'GET'))

    @classmethod
    def api_get_app_summary(cls, app_guid):
        return api.api_get_app_details(app_guid)

    @classmethod
    def api_get_apps_list(cls, space_guid):
        response = api.api_get_apps(space_guid)
        applications = []
        for app in response:
            applications.append(cls(name=app['name'], guid=app['guid']))
        return applications

    @staticmethod
    def compare_details(a, b):
        compare_elements = lambda x, y: collections.Counter(x) == collections.Counter(y)

        def compare_domains(cli, console):
            cli_domains = []
            console_domains = []
            for i in cli:
                cli_domains.append(i['host'] + "." + i['domain']['name'])
            for i in console:
                console_domains.append(i['host'] + "." + i['domain']['name'])
            return compare_elements(cli_domains, console_domains)

        def compare_services(cli, console):
            cli_services = []
            console_services = []
            for i in cli:
                cli_services.append(i['name'])
            for i in console:
                console_services.append(i['name'])
            return compare_elements(cli_services, console_services)

        different_details = []
        if a['memory'] != b['memory']:
            different_details.append('memory')
        if a['disk_quota'] != b['disk_quota']:
            different_details.append('disk_quota')
        if a['running_instances'] != b['running_instances']:
            different_details.append('running_instances')
        if a['instances'] != b['instances']:
            different_details.append('instances')
        if not compare_domains(a['routes'], b['routes']):
            different_details.append('domains')
        if not compare_services(a['services'], b['services']):
            different_details.append('services_bound')
        if a['detected_buildpack'] != b['detected_buildpack']:
            different_details.append('detected_buildpack')
        if a['command'] != b['command']:
            different_details.append('start_command')
        if a['environment_json'] != b['environment_json']:
            different_details.append('environment')
        if a['package_updated_at'] != b['package_updated_at']:
            different_details.append('updated_at')
        return different_details



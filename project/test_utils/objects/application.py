import base64
import collections
import json
import os
import re
from urllib.parse import urlparse

import requests
import yaml

import test_utils.cli.cloud_foundry as cf
from test_utils.api_calls import service_catalog_api_calls as api
from test_utils.logger import get_logger
from test_utils import config
from test_utils.objects.user import get_admin_client


logger = get_logger("application")


__all__ = ["Application", "github_get_file_content"]


def github_get_file_content(repository, path, owner="intel-data"):
    endpoint = "https://api.github.com/repos/{}/{}/contents/{}".format(owner, repository, path)
    logger.info("Retrieving content of {}/{}/{}".format(owner, repository, path))
    auth = config.TEST_SETTINGS["GITHUB_AUTH"]
    response = requests.get(endpoint, auth=auth)
    if response.status_code != 200:
        raise Exception("Github API response is {} {}".format(response.status_code, response.text))
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
        self._state = state
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
            self.manifest_path = os.path.join(local_path, self.MANIFEST_NAME)
            with open(self.manifest_path) as f:
                self.manifest = yaml.load(f.read())
            if "path" in self.manifest["applications"][0]:
                self.local_jar = self.local_jar + "/" + self.manifest["applications"][0]["path"]
        self._broker_guid = None

    def __repr__(self):
        return "{0} (name={1})".format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return (self.name == other.name and self.state == other.state and self.instances == other.instances and
                self.memory == other.memory and self.disk == other.disk and self.urls == other.urls)

    @property
    def broker_guid(self):
        if self._broker_guid is None:
            cf_env = self.cf_env()
            self._broker_guid = cf_env["VCAP_SERVICES"]["hdfs"][0]["credentials"]["uri"].split("/")[-2]
        return self._broker_guid

    @property
    def is_started(self):
        if self._state is None:
            return None
        if self._state.upper() == "STARTED":
            return True
        return False

    def __save_manifest(self):
        with open(self.manifest_path, "w") as f:
            f.write(yaml.dump(self.manifest))

    @classmethod
    def delete_test_apps(cls):
        while len(cls.TEST_APPS) > 0:
            app = cls.TEST_APPS[0]
            app.cf_delete()

    @classmethod
    def get_list_from_settings(cls, settings_yml, state="started"):
        applications = []
        settings = yaml.load(settings_yml)
        for app_info in settings["applications"] + settings["user_provided_service_instances"] + settings["service_brokers"]:
            tmp_name = ""
            if "credentials" in app_info.keys():
                if "host" in app_info["credentials"].keys():
                    tmp_name = re.split('[.]', urlparse(app_info["credentials"]["host"]).hostname)[0]
                elif "hueUrl" in app_info["credentials"].keys():
                    tmp_name = re.split('[.]', urlparse(app_info["credentials"]["hueUrl"]).hostname)[0]
            elif "broker_url" in app_info.keys():
                tmp_name = re.split('[.]', urlparse(app_info["broker_url"]).hostname)[0]
            if not tmp_name:
                tmp_name = app_info["name"]
            applications.append(cls(name=tmp_name, state=state))
        return applications

    @classmethod
    def cf_api_get_list(cls, space_guid):
        """Get list of applications from Cloud Foundry API"""
        applications = []
        cf_space_summary = cf.cf_api_space_summary(space_guid)
        for app_data in cf_space_summary["apps"]:
            app = cls(name=app_data["name"], state=app_data["state"], memory=app_data["memory"],
                      disk=app_data["disk_quota"], instances="{}/{}".format(app_data["running_instances"],
                                                                            app_data["instances"]),
                      urls=tuple(app_data["urls"]), guid=app_data["guid"])
            applications.append(app)
        return applications

    @classmethod
    def cf_get_app_summary(cls, app_guid):
        return cf.cf_api_app_summary(app_guid)

    @classmethod
    def api_get_app_summary(cls, app_guid, client=None):
        client = client or get_admin_client()
        return api.api_get_app_summary(client, app_guid)

    @classmethod
    def api_get_apps_list(cls, space_guid, client=None):
        client = client or get_admin_client()
        response = api.api_get_apps(client, space_guid)
        applications = []
        for app in response:
            applications.append(cls(name=app['name'], guid=app['guid']))
        return applications

    def api_get(self, endpoint, url=None):
        url = url or self.urls[0]
        url = "http://" + url + endpoint
        logger.info("---------------------------------- GET {} ----------------------------------".format(url))
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

    def cf_delete(self):
        self.TEST_APPS.remove(self)
        return cf.cf_delete(self.name)

    def change_name_in_manifest(self, new_name):
        self.manifest["applications"][0]["name"] = new_name
        self.__save_manifest()

    def change_topic_in_manifest(self, new_topic):
        self.manifest["applications"][0]["env"]["TOPICS"] = new_topic
        self.__save_manifest()

    def change_consumer_group_in_manifest(self, new_consumer_group):
        self.manifest["applications"][0]["env"]["CONSUMER_GROUP"] = new_consumer_group

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



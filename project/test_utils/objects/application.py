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

import base64
import json
import os
import re

import requests
import yaml

import test_utils.cli.cloud_foundry as cf
import test_utils.platform_api_calls as api
from test_utils import TEST_SETTINGS, get_logger


logger = get_logger("application")


__all__ = ["Application", "github_get_file_content"]


def github_get_file_content(repository, path, owner="trustedanalytics"):
    endpoint = "https://api.github.com/repos/{}/{}/contents/{}".format(owner, repository, path)
    logger.info("Retrieving content of {}/{}/{}".format(owner, repository, path))
    auth = TEST_SETTINGS["GITHUB_AUTH"]
    response = requests.get(endpoint, auth=auth)
    if response.status_code != 200:
        raise Exception("Github API response is {} {}".format(response.status_code, response.text))
    encoding = response.encoding
    response_content = response.content.decode(encoding)
    return base64.b64decode(json.loads(response_content)["content"])


class Application(object):

    MANIFEST_NAME = "manifest.yml"
    TEST_APPS = []

    def __init__(self, name, space_guid=None, guid=None, local_path=None, state=None, instances=None,
                 memory=None, service_names=(), disk=None, urls=(), topic=None):
        """local_path - directory where application manifest is located"""
        self.name, self.guid, self.space_guid = name, guid, space_guid
        self.instances, self.memory, self.disk = instances, memory, disk
        self.service_names, self.urls = tuple(service_names), tuple(urls)
        self.topic = topic
        self._state = state
        self._local_path = self._local_jar = local_path
        if self._local_path is not None:
            self.manifest_path = os.path.join(local_path, self.MANIFEST_NAME)
            with open(self.manifest_path) as f:
                self.manifest = yaml.load(f.read())
            if "path" in self.manifest["applications"][0]:
                self._local_jar += ("/" + self.manifest["applications"][0]["path"])

    def __repr__(self):
        return "{0} (name={1}, guid={2})".format(self.__class__.__name__, self.name, self.guid)

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

    def change_name_in_manifest(self, new_name):
        self.manifest["applications"][0]["name"] = new_name
        self.__save_manifest()

    def change_topic_in_manifest(self, new_topic):
        self.manifest["applications"][0]["env"]["TOPICS"] = new_topic
        self.__save_manifest()

    def change_consumer_group_in_manifest(self, new_consumer_group):
        self.manifest["applications"][0]["env"]["CONSUMER_GROUP"] = new_consumer_group
        self.__save_manifest()

    def application_api_request(self, endpoint, method="GET", scheme="http", url=None, data=None, params=None):
        """Send a request to application api"""
        url = url or self.urls[0]
        url = "{}://{}/{}".format(scheme, url, endpoint)
        request_method = getattr(requests, method.lower())
        response = request_method(
            url=url,
            data=data,
            params=params
        )
        logger.info("------------------------------ {} {} ------------------------------".format(method.upper(), url))
        if not response.ok:
            raise Exception("Response code is {} {}".format(response.status_code, response.text))
        if "DOCTYPE HTML" in response.text:
            return response.text
        return json.loads(response.text)

    @staticmethod
    def _get_details_from_response(response):
        def prim_environment_json(env_json):
            # this unification of responses is necessary because of unimplemented pattern parameters (^) in pyswagger
            if isinstance(env_json, str):
                if env_json.startswith("{"):
                    env_json = env_json.replace("'{", "{").replace("}'", "}").replace("'", "\"").replace("\\n", "")
                    env_json = json.loads(env_json)
                    env_json = {k: v for k, v in env_json.items()}
                return env_json
            return {k: prim_environment_json(v) for k, v in env_json.items()}
        return {
            "command": response["command"],
            "detected_buildpack": response["detected_buildpack"],
            "disk_quota": response["disk_quota"],
            "domains": sorted(["{}.{}".format(item["host"], item["domain"]["name"]) for item in response["routes"]]),
            "environment_json": prim_environment_json(response["environment_json"]),
            "instances": response["instances"],
            "memory": response["memory"],
            "package_updated_at": response["package_updated_at"],
            "running_instances": response["running_instances"],
            "service_names": sorted([service["name"] for service in response["services"]])
        }

    # -------------------------------- platform api -------------------------------- #

    @classmethod
    def api_get_list(cls, space_guid, service_label=None, client=None):
        """Get list of applications from Console / service-catalog API"""
        response = api.api_get_filtered_applications(space_guid, service_label, client=client)
        applications = []
        for app in response:
            application = cls(name=app["name"], space_guid=space_guid, guid=app["guid"], state=app["state"],
                              urls=app["urls"], service_names=app["service_names"])
            applications.append(application)
        return applications

    def api_get_summary(self, client=None):
        response = api.api_get_app_summary(self.guid, client=client)
        return self._get_details_from_response(response)

    def api_delete(self, cascade=True, client=None):
        api.api_delete_app(self.guid, cascade=cascade, client=None)

    def api_get_orphan_services(self, client=None):
        response = api.api_get_app_orphan_services(self.guid, client=client)
        # TODO should probably return a list of ServiceInstance objects initialized from response

    def api_restage_app(self, new_name, client=None):
        # TODO
        api.api_restage_app(self.guid, new_name, client=client)
        self.name = new_name

    def api_get_service_bindings(self, client=None):
        # TODO
        response = api.api_get_app_bindings(self.guid, client=client)
        bindings = []
        for data in response:
            bindings.append({
                "guid": data["metadata"]["guid"],
                "app_guid": self.guid,
                "service_instance_guid": data["entity"]["service_instance_guid"]
            })
        return bindings

    def api_create_service_binding(self, service_instance_guid, client=None):
        # TODO
        api.api_create_service_binding(self.guid, service_instance_guid, client=client)

    @staticmethod
    def api_delete_service_binding(binding_guid, client=None):
        # TODO
        api.api_delete_service_binding(binding_guid, client=client)

    # -------------------------------- cf api -------------------------------- #

    @classmethod
    def from_cf_api_space_summary_response(cls, response, space_guid):
        applications = []
        for app_data in response["apps"]:
            app = cls(name=app_data["name"], space_guid=space_guid, state=app_data["state"], memory=app_data["memory"],
                      disk=app_data["disk_quota"], instances="{}/{}".format(app_data["running_instances"],
                                                                            app_data["instances"]),
                      urls=tuple(app_data["urls"]), guid=app_data["guid"])
            applications.append(app)
        return applications

    @classmethod
    def cf_api_get_list(cls, space_guid):
        """Get list of applications from Cloud Foundry API"""
        response = cf.cf_api_space_summary(space_guid)
        return cls.from_cf_api_space_summary_response(response, space_guid)

    def cf_api_get_summary(self):
        response = cf.cf_api_app_summary(self.guid)
        return self._get_details_from_response(response)

    def cf_api_env(self):
        response = cf.cf_api_env(self.guid)
        return {
            "VCAP_SERVICES": response["system_env_json"]["VCAP_SERVICES"],
            "VCAP_APPLICATION": response["application_env_json"]["VCAP_APPLICATION"]
        }

    # -------------------------------- cf cli -------------------------------- #

    @classmethod
    def delete_test_apps(cls):
        while len(cls.TEST_APPS) > 0:
            app = cls.TEST_APPS[0]
            app.cf_delete()

    def cf_push(self, organization, space):
        cf.cf_target(organization.name, space.name)
        output = cf.cf_push(self._local_path, self._local_jar)
        self.TEST_APPS.append(self)
        for line in output.split("\n"):
            if line[0:5] == "urls:":
                self.urls = (re.split(r'urls: ', line)[1],)
        self.guid = next(app.guid for app in self.api_get_list(space.guid) if app.name == self.name)

    def cf_delete(self):
        if self in self.TEST_APPS:
            self.TEST_APPS.remove(self)
        return cf.cf_delete(self.name)

    def cf_env(self):
        output = cf.cf_env(self.name)
        start = re.search("^\{$", output, re.MULTILINE).start()
        end = re.search("^\}$", output, re.MULTILINE).end()
        return json.loads(output[start:end])


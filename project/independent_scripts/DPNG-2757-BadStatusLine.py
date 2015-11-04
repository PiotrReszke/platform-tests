#!/usr/bin/python3
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

import argparse
from datetime import datetime
import json
import logging
import time

import requests  # use requests==2.7.0


parser = argparse.ArgumentParser()
parser.add_argument("-e", help="environment (e.g. sprint.gotapaas.com)", required=True)
parser.add_argument("-n", help="how many iterations", type=int, required=True)
args = parser.parse_args()


log_file = "{}-{}.log".format(args.e, datetime.now().strftime("%Y%m%d-%H%M%S.%f"))
print("Logging to file {}".format(log_file))
logging.basicConfig(filename=log_file, level=logging.DEBUG)
logger = logging.getLogger("trigger BSL")
requests.packages.urllib3.disable_warnings()

CONSOLE_ENDPOINT = "https://console.{}".format(args.e)
CF_ENDPOINT = "https://api.{}".format(args.e)
CONSOLE_LOGIN_ENDPOINT = "http://login.{}/login.do".format(args.e)
CF_TOKEN_ENDPOINT = "https://login.{}/oauth/token".format(args.e)
USERNAME = "trusted.analytics.tester@gmail.com"
PASS = "super-secret-tester-pass"
N = args.n
logger.info("{} iterations".format(N))


def handle_request(request, session, description=""):
    request = session.prepare_request(request)
    logged_body = request.body
    if logged_body is None:
        logged_body = ""
    logger.debug("\n".join([
        description,
        "----------------Request------------------",
        "URL: {} {}".format(request.method, request.url),
        "Headers: {}".format(request.headers),
        "Body: {}".format(logged_body),
        "-----------------------------------------"
    ]))
    response = session.send(request)
    body = response.text
    logger.debug("\n".join([
        "\n----------------Response------------------",
        "Status code: {}".format(response.status_code),
        "Headers: {}".format(response.headers),
        "Content: {}".format(body),
        "-----------------------------------------\n"
    ]))
    if not response.ok:
        raise AssertionError("{} {}".format(response.status_code, response.text))
    try:
        return json.loads(response.text)
    except ValueError:
        return response.text


def get_cf_token(session):
    request = requests.Request(
        method="POST",
        url=CF_TOKEN_ENDPOINT,
        headers={
            "Authorization": "Basic Y2Y6",
            "Accept": "application/json"
        },
        data={"username": USERNAME, "password": PASS, "grant_type": "password"}
    )
    response = handle_request(request, session, description="Get cf token")
    return response["access_token"]


def cleanup(org_list):
    cf_session = requests.Session()
    cf_session.verify = False
    token = get_cf_token(cf_session)
    token_retrieval_time = time.time()
    for org in org_list:
        if time.time() - token_retrieval_time > 298:
            token = get_cf_token(cf_session)
        request = requests.Request(
            method="DELETE",
            url="{}/v2/organizations/{}".format(CF_ENDPOINT, org.guid),
            headers={"Authorization": "Bearer {}".format(token)},
            params={"recursive": "true", "async": "false"}
        )
        handle_request(request, cf_session, description="Delete org with CF")


class Organization(object):

    def __init__(self, name, guid):
        self.name = name
        self.guid = guid

    @classmethod
    def api_create(cls, session):
        name = "test_org_{}".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        request = requests.Request(
            method="POST",
            url="{}/rest/orgs".format(CONSOLE_ENDPOINT),
            json={"name": name}
        )
        response = handle_request(request, session, description="Create org")
        return cls(name=name, guid=response.strip('"'))

    def api_delete(self, session):
        request = requests.Request(
            method="DELETE",
            url="{}/rest/orgs/{}".format(CONSOLE_ENDPOINT, self.guid)
        )
        handle_request(request, session, description="delete_org")


class Space(object):

    def __init__(self, name, guid, org_guid):
        self.name = name
        self.guid = guid
        self.org_guid = org_guid

    @classmethod
    def api_create(cls, session, org_guid):
        name = "test-space-{}".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        request = requests.Request(
            method="POST",
            url="{}/rest/spaces".format(CONSOLE_ENDPOINT),
            json={"name": name, "org_guid": org_guid}
        )
        response = handle_request(request, session, description="Create space")
        return cls(name=name, guid=response, org_guid=org_guid)


class GatewayInstance(object):

    def __init__(self, guid, name, space_guid, org_guid):
        self.guid, self.name = guid, name
        self.space_guid, self.org_guid = space_guid, org_guid

    @classmethod
    def api_create(cls, session, space_guid, org_guid):
        st_request = requests.Request(
            method="GET",
            url="{}/rest/services".format(CONSOLE_ENDPOINT),
            params={"space": space_guid}
        )
        response = handle_request(st_request, session, description="Get list of services")
        gateway_data = next(st_data["entity"]
                            for st_data in response if st_data["entity"]["label"] == "gateway")

        name = "test-gateway-{}".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        # this is the request that causes BadStatusLine most often
        si_request = requests.Request(
            method="POST",
            url="{}/rest/service_instances".format(CONSOLE_ENDPOINT),
            json={
                "name": name,
                "organization_guid": org_guid,
                "service_plan_guid": gateway_data["service_plans"][0]["metadata"]["guid"],
                "space_guid": space_guid,
                "parameters": {"name": name}
            }
        )
        response = handle_request(si_request, session, description="Create gateway instance")
        return cls(guid=response["metadata"]["guid"], name=name, space_guid=space_guid, org_guid=org_guid)

    def api_delete(self, session):
        request = requests.Request(
            method="DELETE",
            url="{}/rest/service_instances/{}".format(CONSOLE_ENDPOINT, self.guid)
        )
        handle_request(request, session, description="Delete service instance")



if __name__ == "__main__":

    admin_session = requests.session()
    admin_session.verify = False

    login_request = requests.Request(
        method="POST",
        url=CONSOLE_LOGIN_ENDPOINT,
        data={"username": USERNAME, "password": PASS},
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    )
    handle_request(login_request, admin_session, description="Authenticate admin")

    orgs = []
    for n in range(N):
        try:
            logger.info("Iteration {}/{}".format(n, N-1))
            org = Organization.api_create(admin_session)
            orgs.append(org)
            space = Space.api_create(admin_session, org.guid)
            gateway = GatewayInstance.api_create(admin_session, space.guid, org.guid)
            gateway.api_delete(admin_session)
        except requests.exceptions.ConnectionError:
            logger.error("BadStatusLine")
            print("BadStatusLine in iteration {}/{}".format(n, N-1))
    cleanup(orgs)
    print("END")


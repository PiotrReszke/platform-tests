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
import multiprocessing
import sys
import time
import traceback

import requests  # use requests==2.7.0


parser = argparse.ArgumentParser()
parser.add_argument("-n", help="number of concurrent processes", type=int, required=True)
parser.add_argument("-e", help="environment (e.g. sprint.gotapaas.com)", required=True)
parser.add_argument("-i", help="number of iterations in each process", type=int, required=True)
parser.add_argument("-p", help="password for trusted.analytics.tester@gmail.com", required=True)
parser.add_argument("-c", help="password for retrieving cf token", required=True)
args = parser.parse_args()


PROCESS_COUNT = args.n
ITERATION_COUNT = args.i



class ApiObject(object):

    CONSOLE_ENDPOINT = "https://console.{}".format(args.e)
    CF_ENDPOINT = "https://api.{}".format(args.e)
    CONSOLE_LOGIN_ENDPOINT = "http://login.{}/login.do".format(args.e)
    CF_LOGIN_ENDPOINT = "https://login.{}/oauth/token".format(args.e)
    USERNAME = "trusted.analytics.tester@gmail.com"
    PASSWORD = args.p
    SESSION = requests.session()
    SESSION.verify = False
    CF_SESSION = requests.session()
    CF_SESSION.verify = False
    CF_TOKEN = None
    TOKEN_RETRIEVAL_TIME = 0
    CF_PASS = args.c

    @classmethod
    def handle_request(cls, logger, request, description=""):
        # select session depending on endpoint (cf or console)
        if "console" in request.url or "login.do" in request.url:
            session = cls.SESSION
        else:
            session = cls.CF_SESSION
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

    @classmethod
    def console_login(cls, logger):
        login_request = requests.Request(
            method="POST",
            url=cls.CONSOLE_LOGIN_ENDPOINT,
            data={"username": cls.USERNAME, "password": cls.PASSWORD},
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        )
        cls.handle_request(logger, login_request, description="Authenticate admin")

    @classmethod
    def get_cf_token(cls, logger):
        if time.time() - cls.TOKEN_RETRIEVAL_TIME > 298:
            request = requests.Request(
                method="POST",
                url=cls.CF_LOGIN_ENDPOINT,
                headers={
                    "Authorization": cls.CF_PASS,
                    "Accept": "application/json"
                },
                data={"username": cls.USERNAME, "password": cls.PASSWORD, "grant_type": "password"}
            )
            response = cls.handle_request(logger, request, description="Get cf token")
            cls.TOKEN_RETRIEVAL_TIME = time.time()
            cls.CF_TOKEN = response["access_token"]
        return cls.CF_TOKEN

    def api_get_latest_events(self, logger, org_guid=None):
        params = {} if org_guid is None else {"org": org_guid}
        request = requests.Request(
            method="GET",
            params=params,
            url="{}/rest/les/events".format(self.CONSOLE_ENDPOINT)
        )
        self.handle_request(logger, request, "get latest events")



class Organization(ApiObject):

    ORGS = []

    def __init__(self, name, guid):
        self.name = name
        self.guid = guid

    @classmethod
    def api_create(cls, logger):
        name = "test_org_{}".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        request = requests.Request(
            method="POST",
            url="{}/rest/orgs".format(cls.CONSOLE_ENDPOINT),
            json={"name": name}
        )
        response = cls.handle_request(logger, request, description="api create org")
        org = cls(name=name, guid=response.strip('"'))
        cls.ORGS.append(org)
        return org

    def cf_delete(self, logger):
        token = self.get_cf_token(logger)
        request = requests.Request(
            method="DELETE",
            url="{}/v2/organizations/{}".format(self.CF_ENDPOINT, self.guid),
            headers={"Authorization": "Bearer {}".format(token)},
            params={"recursive": "true", "async": "false"}
        )
        self.handle_request(logger, request, description="cf delete org")
        self.ORGS.remove(self)

    def api_get_metrics(self, logger):
        request = requests.Request(
            method="GET",
            url="{}/rest/orgs/{}/metrics".format(self.CONSOLE_ENDPOINT, self.guid)
        )
        self.handle_request(logger, request, description="api get org metrics")


class User(ApiObject):

    def __init__(self, name, guid):
        self.name = name
        self.guid = guid

    @classmethod
    def api_add_admin_to_org(cls, logger, org_guid):
        request = requests.Request(
            method="POST",
            url="{}/rest/orgs/{}/users".format(cls.CONSOLE_ENDPOINT, org_guid),
            json={"username": cls.USERNAME, "org_guid": org_guid, "roles": ["managers"]}
        )
        response=cls.handle_request(logger, request, "api add admin to org")
        return cls(name=response["username"], guid=response["guid"])

    @classmethod
    def api_get_list_in_org(cls, logger, org_guid):
        request = requests.Request(
            method="GET",
            url="{}/rest/orgs/{}/users".format(cls.CONSOLE_ENDPOINT, org_guid)
        )
        response = cls.handle_request(logger, request, "api get users in org")
        users = []
        for user_data in response:
            users.append(cls(name=user_data["username"], guid=user_data["guid"]))
        return users


def worker(process_num):
    LOG_FILE = "{}-{}-{}.log".format(args.e, process_num, datetime.now().strftime("%Y%m%d-%H%M%S"))
    logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)
    logger = logging.getLogger("trigger BSL {}".format(process_num))
    requests.packages.urllib3.disable_warnings()
    print("logging to file {}".format(LOG_FILE))

    ApiObject.console_login(logger)
    for n in range(ITERATION_COUNT):
        try:
            logger.info("Iteration {}/{}".format(n, ITERATION_COUNT-1))
            org = Organization.api_create(logger)
            User.api_add_admin_to_org(logger, org.guid)
            for i in range(5):
                User.api_get_list_in_org(logger, org.guid)
            org.api_get_metrics(logger)
            org.api_get_latest_events(logger)
            org.api_get_latest_events(logger, org.guid)
            org.cf_delete(logger)
        except requests.exceptions.ConnectionError:
            logger.error(traceback.format_exc())
            tb = traceback.extract_tb(sys.exc_info()[-1])[-4]
            print("{} BadStatusLine in worker {}, method {}, line {}".format(datetime.now().strftime('%H:%M:%S.%f'),
                                                                             process_num, tb[2], tb[1]))
    logger.info("----------- CLEANUP -----------")
    for org in Organization.ORGS:
        org.cf_delete()



if __name__ == "__main__":
    jobs = []
    for i in range(PROCESS_COUNT):
        p = multiprocessing.Process(target=worker, args=(i,))
        jobs.append(p)
        p.start()
    for j in jobs:
        j.join()
    print("END")


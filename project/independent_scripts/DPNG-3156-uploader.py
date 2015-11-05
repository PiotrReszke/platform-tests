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
import csv
from datetime import datetime
import json
import logging
import os
import time

import requests  # use requests==2.7.0


parser = argparse.ArgumentParser()
parser.add_argument("-e", help="environment (e.g. sprint.gotapaas.com)", required=True)
parser.add_argument("-n", help="number of iterations", type=int, required=True)
# parser.add_argument("-p", help="password for trusted.analytics.tester@gmail.com", required=True)
# parser.add_argument("-c", help="password for retrieving cf token", required=True)
args = parser.parse_args()


LOG_FILE = "{}-{}.log".format(args.e, datetime.now().strftime("%Y%m%d-%H%M%S"))
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)
LOGGER = logging.getLogger("uploader test")
requests.packages.urllib3.disable_warnings()
ITERATION_COUNT = args.n


def create_csv_file(file_path, column_count, row_count):
    with open(file_path, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["COL_{}".format(i) for i in range(column_count)])
        for i in range(row_count):
            csv_writer.writerow([str(j) * 20 for j in range(column_count)])


class ApiObject(object):

    CONSOLE_ENDPOINT = "https://console.{}".format(args.e)
    CF_ENDPOINT = "https://api.{}".format(args.e)
    CONSOLE_LOGIN_ENDPOINT = "http://login.{}/login.do".format(args.e)
    CF_LOGIN_ENDPOINT = "https://login.{}/oauth/token".format(args.e)
    USERNAME = "trusted.analytics.tester@gmail.com"
    PASSWORD = "super-secret-tester-pass"
    SESSION = requests.session()
    SESSION.verify = False
    CF_SESSION = requests.session()
    CF_SESSION.verify = False
    CF_TOKEN = None
    TOKEN_RETRIEVAL_TIME = 0
    CF_PASS = "Basic Y2Y6"

    @classmethod
    def handle_request(cls, request, description=""):
        # select session depending on endpoint (cf or console)
        if "console" in request.url or "login.do" in request.url:
            session = cls.SESSION
        else:
            session = cls.CF_SESSION
        request = session.prepare_request(request)
        logged_body = request.body
        if logged_body is None:
            logged_body = ""
        LOGGER.debug("\n".join([
            description,
            "----------------Request------------------",
            "URL: {} {}".format(request.method, request.url),
            "Headers: {}".format(request.headers),
            "Body: {}".format(logged_body),
            "-----------------------------------------"
        ]))
        response = session.send(request)
        body = response.text
        LOGGER.debug("\n".join([
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
    def console_login(cls):
        login_request = requests.Request(
            method="POST",
            url=cls.CONSOLE_LOGIN_ENDPOINT,
            data={"username": cls.USERNAME, "password": cls.PASSWORD},
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        )
        cls.handle_request(login_request, description="Authenticate admin")

    @classmethod
    def get_cf_token(cls):
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
            response = cls.handle_request(request, description="Get cf token")
            cls.TOKEN_RETRIEVAL_TIME = time.time()
            cls.CF_TOKEN = response["access_token"]
        return cls.CF_TOKEN


class Organization(ApiObject):

    ORGS = []

    def __init__(self, name, guid):
        self.name = name
        self.guid = guid

    @classmethod
    def api_create(cls):
        name = "test_org_{}".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        request = requests.Request(
            method="POST",
            url="{}/rest/orgs".format(cls.CONSOLE_ENDPOINT),
            json={"name": name}
        )
        response = cls.handle_request(request, description="Create org")
        org = cls(name=name, guid=response.strip('"'))
        cls.ORGS.append(org)
        return org

    def cf_delete(self):
        token = self.get_cf_token()
        request = requests.Request(
            method="DELETE",
            url="{}/v2/organizations/{}".format(self.CF_ENDPOINT, self.guid),
            headers={"Authorization": "Bearer {}".format(token)},
            params={"recursive": "true", "async": "false"}
        )
        self.handle_request(request, description="cf delete org")
        self.ORGS.remove(self)


class Transfer(ApiObject):

    TRANSFERS = []

    def __init__(self, title, state, transfer_id, org_guid):
        self.title = title
        self.state = state
        self.transfer_id = transfer_id
        self.org_guid = org_guid

    @classmethod
    def api_create_from_local_file(cls, org_guid, file_path, category="other", is_public=False):
        title = "test_{}".format(datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        _, file_name = os.path.split(file_path)
        request = requests.Request(
            method="POST",
            url="{}/rest/upload/{}".format(cls.CONSOLE_ENDPOINT, org_guid),
            data={"title": title, "orgUUID": org_guid, "category": category, "publicRequest": str(is_public).lower()},
            files={"file": (file_path, open(file_path, "rb"), "application/vnd.ms-excel")}
        )
        cls.handle_request(request, description="Create transfer from local file")
        transfer = next(t for t in cls.api_get_list([org_guid]) if t.title == title)
        cls.TRANSFERS.append(transfer)
        # DataSet.TRANSFERS_AND_DS[transfer] = None
        return transfer

    @classmethod
    def api_get_list(cls, org_guid_list):
        request = requests.Request(
            method="GET",
            url="{}/rest/das/requests".format(cls.CONSOLE_ENDPOINT),
            params={"orgs": ",".join(org_guid_list)}
        )
        transfers = []
        response = cls.handle_request(request, description="Get transfer list")
        for transfer_data in response:
            transfers.append(cls(title=transfer_data["title"], state=transfer_data["state"],
                                 transfer_id=transfer_data["id"], org_guid=transfer_data["orgUUID"]))
        return transfers

    @classmethod
    def api_get(cls, transfer_id):
        request = requests.Request(
            method="GET",
            url="{}/rest/das/requests/{}".format(cls.CONSOLE_ENDPOINT, transfer_id)
        )
        response = cls.handle_request(request, description="Get transfer")
        return cls(title=response["title"], state=response["state"], transfer_id=response["id"],
                   org_guid=response["orgUUID"])

    def api_delete(self):
        request = requests.Request(
            method="DELETE",
            url="{}/rest/das/requests/{}".format(self.CONSOLE_ENDPOINT, self.transfer_id)
        )
        self.handle_request(request, description="Delete transfer")

    def api_ensure_finished(self, timeout=120):
        start = time.time()
        while time.time() - start < timeout:
            transfer = self.api_get(self.transfer_id)
            if transfer.state == "FINISHED":
                self.state = "FINISHED"
                return
        raise TimeoutError("Transfer did not finish in {}s".format(timeout))


def cleanup():
    LOGGER.info("---------- CLEANUP ----------")
    for transfer in Transfer.TRANSFERS:
        transfer.api_delete()
    for org in Organization.ORGS:
        org.cf_delete()


if __name__ == "__main__":
    print("Logging to file {}".format(LOG_FILE))
    csv_file_name = "test.csv"
    create_csv_file(csv_file_name, 10, 10)

    ApiObject.console_login()
    for i in range(ITERATION_COUNT):
        try:
            org = Organization.api_create()
            transfer = Transfer.api_create_from_local_file(org.guid, csv_file_name)
            # transfer.api_ensure_finished()
            # data_set = DataSet.api_get_from_transfer(transfer)
        except AssertionError as e:
            print("Iteration {}: Uploader exception: \n{}".format(i, e.args[0]))
    cleanup()
    os.remove(csv_file_name)






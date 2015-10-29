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

import abc
import json
import time

import requests

from . import config, log_http_request, log_http_response


__all__ = ["UnexpectedResponseError", "PlatformApiClient", "ConsoleClient",
           "AppClient", "CfApiClient"]


class UnexpectedResponseError(AssertionError):
    def __init__(self, status, error_message, message=None):
        message = message or "{} {}".format(status, error_message)
        super(UnexpectedResponseError, self).__init__(message)
        self.status = status
        self.error_message = error_message


class PlatformApiClient(metaclass=abc.ABCMeta):
    """Base class for HTTP clients"""

    _CLIENTS = {}

    @abc.abstractmethod
    def __init__(self, platform_username, platform_password):
        self._username = platform_username
        self._password = platform_password
        self._domain = config.CONFIG["domain"]
        self._login_endpoint = "login.{}".format(self._domain)
        self._session = requests.Session()
        proxy = config.CONFIG["proxy"]
        if proxy is not None:
            self._session.proxies = {"https": proxy, "http": proxy}
        self._session.verify = config.CONFIG["ssl_validation"]

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self._username)

    @classmethod
    def get_admin_client(cls):
        admin_username = config.CONFIG["admin_username"]
        admin_password = config.CONFIG["admin_password"]
        return cls.get_client(admin_username, admin_password)

    @classmethod
    def get_client(cls, username, password=None):
        if cls._CLIENTS.get(username) is None:
            client_type = config.CONFIG["client_type"]
            if client_type == "console":
                cls._CLIENTS[username] = ConsoleClient(username, password)
            elif client_type == "app":
                cls._CLIENTS[username] = AppClient(username, password)
        return cls._CLIENTS[username]

    def request(self, method, endpoint, headers=None, files=None, params=None, data=None, body=None, log_msg=""):
        request = requests.Request(
            method=method.upper(),
            url=self.url + endpoint,
            headers=headers,
            files=files,
            data=data,
            params=params,
            json=body
        )
        request = self._session.prepare_request(request)
        log_http_request(request, self._username, self._password, description=log_msg)
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        if response.text == "":
            return response.text
        return json.loads(response.text)

    def download_file(self, endpoint, target_file_path):
        """Download (large) file in chunks and save it to target_file_path."""
        request = requests.Request("GET", url=self.url + endpoint)
        request = self._session.prepare_request(request)
        log_http_request(request, self._username, description="PLATFORM: Download file")
        response = self._session.send(request, stream=True)
        log_http_response(response, logged_body_length=0)  # the body is a long stream of binary data
        with open(target_file_path, 'w+b') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()


class ConsoleClient(PlatformApiClient):
    """HTTP client which calls Platform API - using console endpoint and cookie-based authentication."""

    def __init__(self, platform_username, platform_password=None):
        super().__init__(platform_username, platform_password)
        if platform_password is not None:
            self.authenticate(platform_password)

    @property
    def url(self):
        return "https://console.{}/".format(self._domain)

    def authenticate(self, password):
        request = requests.Request(
            method="POST",
            url="{}://{}/login.do".format(config.CONFIG["login.do_scheme"], self._login_endpoint),
            data={"username": self._username, "password": password},
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        )
        request = self._session.prepare_request(request)
        log_http_request(request, self._username, self._password, description="Authenticate user")
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok or "forgotPasswordLink" in response.text:
            raise UnexpectedResponseError(response.status_code, response.text)


class AppClient(PlatformApiClient):
    """HTTP client which calls APIs of specific applications (bypassing console) using token-based authentication"""

    _TOKEN_EXPIRY_TIME = 298  # (in seconds) 5 minutes minus 2s buffer
    GUID_PATTERN = "([a-z]|[0-9]|-)*"
    APP_ENDPOINT_MAP = {  # matches application names with API endpoint patterns
        "app-launcher-helper": lambda x: "atkinstances" in x,
        "das": lambda x: x.startswith("rest/das"),
        "data-catalog": lambda x: x.startswith("rest/datasets"),
        "fileserver": lambda x: x.startswith("/files"),
        "hive": lambda x: x.startswith("rest/tables"),
        "latest-events-service": lambda x: x.startswith("rest/les"),
        "metrics-provider": lambda x: "metrics" in x,
        "service-catalog": lambda x: x.startswith("rest/service"),
        "user-management": lambda x: (("orgs" in x and "atkinstances" not in x and "metrics" not in x) or
                                      ("spaces" in x) or ("invitations" in x) or ("registrations" in x))
    }

    def __init__(self, platform_username, platform_password):
        super().__init__(platform_username, platform_password)
        self._token = None
        self._token_retrieval_time = 0
        self._application_name = None
        if platform_password is not None:
            self._get_token()

    @property
    def url(self):
        return "http://{}.{}/".format(self._application_name, self._domain)

    def _get_token(self):
        path = "https://{}/oauth/token".format(self._login_endpoint)
        headers = {
            "Authorization": config.CONFIG["login_token"],
            "Accept": "application/json"
        }
        data = {"username": self._username, "password": self._password, "grant_type": "password"}
        request = requests.Request("POST", path, data=data, headers=headers)
        request = self._session.prepare_request(request)
        self._token_retrieval_time = time.time()
        log_http_request(request, self._username, self._password, "Retrieve cf token")
        response = self._session.send(request)
        log_http_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        self._token = "Bearer {}".format(json.loads(response.text)["access_token"])

    def request(self, method, endpoint, headers=None, files=None, params=None, data=None, body=None, log_msg=""):
        # check that token has not expired
        if (self._token is not None) and (time.time() - self._token_retrieval_time > self._TOKEN_EXPIRY_TIME):
            self._get_token()
        headers = {} if headers is None else headers
        headers["Authorization"] = self._token
        self._application_name = next((k for k, v in self.APP_ENDPOINT_MAP.items() if v(endpoint)), "")
        return super().request(method, endpoint, headers, files, params, data, body, log_msg)


class CfApiClient(AppClient):
    """HTTP client for CF api calls. Uses token-based authentication."""

    _CF_API_CLIENT = None

    def __init__(self, platform_username, platform_password):
        super().__init__(platform_username, platform_password)

    @property
    def url(self):
        return "https://api.{}/v2/".format(config.CONFIG["domain"])

    @classmethod
    def get_client(cls):
        if cls._CF_API_CLIENT is None:
            admin_username = config.CONFIG["admin_username"]
            admin_password = config.CONFIG["admin_password"]
            cls._CF_API_CLIENT = cls(admin_username, admin_password)
        return cls._CF_API_CLIENT

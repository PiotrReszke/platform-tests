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

from . import config, get_logger


__all__ = ["UnexpectedResponseError", "PlatformApiClient", "ConsoleClient", "AppClient", "CfApiClient"]


logger = get_logger("api client")


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
        self._domain = config.get_config_value("api_endpoint")
        self._login_endpoint = config.get_config_value("login_endpoint")
        self._session = requests.Session()
        proxy = config.TEST_SETTINGS["TEST_PROXY"]
        if proxy is not None:
            self._session.proxies = {"https": proxy, "http": proxy}
        if config.TEST_SETTINGS["TEST_DISABLE_SSL_VALIDATION"] is True:
            self._session.verify = False

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self._username)

    @classmethod
    def get_admin_client(cls):
        admin_username = config.TEST_SETTINGS["TEST_USERNAME"]
        admin_password = config.TEST_SETTINGS["TEST_PASSWORD"]
        return cls.get_client(admin_username, admin_password)

    @classmethod
    def get_client(cls, username, password=None):
        if cls._CLIENTS.get(username) is None:
            client_type = config.TEST_SETTINGS["TEST_CLIENT_TYPE"]
            if client_type == "console":
                cls._CLIENTS[username] = ConsoleClient(username, password)
            elif client_type == "app":
                cls._CLIENTS[username] = AppClient(username, password)
        return cls._CLIENTS[username]

    def request(self, method, endpoint, headers=None, params=None, data=None, body=None):
        request = requests.Request(
            method=method.upper(),
            url=self.url + endpoint,
            headers=headers,
            data=data,
            params=params,
            json=body
        )
        request = self._session.prepare_request(request)
        self._log_request(request)
        response = self._session.send(request)
        self._log_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        if response.text == "":
            return response.text
        return json.loads(response.text)

    def download_file(self, endpoint, target_file_path):
        """Download (large) file in chunks and save it to target_file_path."""
        request = requests.Request("GET", url=self.url + endpoint)
        request = self._session.prepare_request(request)
        self._log_request(request)
        response = self._session.send(request, stream=True)
        self._log_response(response, log_body=False)  # the body is a long stream of binary data
        with open(target_file_path, 'w+b') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()

    def _log_request(self, prepared_request):
        body = prepared_request.body
        if self._password and body:
            body = body.replace(self._password, "[SECRET]")
        msg = [
            "\n----------------Request------------------",
            "Client name: {}".format(self._username),
            "URL: {} {}".format(prepared_request.method, prepared_request.url),
            "Headers: {}".format(prepared_request.headers),
            "Body: {}".format(body),
            "-----------------------------------------\n"
        ]
        logger.debug("\n".join(msg))

    @staticmethod
    def _log_response(response, log_body=True):
        body = response.text if log_body else ""
        msg = [
            "\n----------------Response------------------",
            "Status code: {}".format(response.status_code),
            "Headers: {}".format(response.headers),
            "Content: {}".format(body),
            "-----------------------------------------\n"
        ]
        logger.debug("\n".join(msg))


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
        logger.info("-------------------- Authenticate user {} --------------------".format(self._username))
        request = requests.Request(
            method="POST",
            url="{}://{}/login.do".format(config.get_config_value("login.do_scheme"), self._login_endpoint),
            data={"username": self._username, "password": password},
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        )
        request = self._session.prepare_request(request)
        self._log_request(request)
        response = self._session.send(request)
        self._log_response(response)
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
        logger.info("-------------------- Retrieve token for user {} --------------------".format(self._username))
        path = "https://{}/oauth/token".format(self._login_endpoint)
        headers = {
            "Authorization": config.TEST_SETTINGS["TEST_LOGIN_TOKEN"],
            "Accept": "application/json"
        }
        data = {"username": self._username, "password": self._password, "grant_type": "password"}
        request = requests.Request("POST", path, data=data, headers=headers)
        request = self._session.prepare_request(request)
        self._token_retrieval_time = time.time()
        self._log_request(request)
        response = self._session.send(request)
        self._log_response(response)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        self._token = "Bearer {}".format(json.loads(response.text)["access_token"])

    def request(self, method, endpoint, headers=None, params=None, data=None, body=None):
        # check that token has not expired
        if (self._token is not None) and (time.time() - self._token_retrieval_time > self._TOKEN_EXPIRY_TIME):
            self._get_token()
        headers = {} if headers is None else headers
        headers["Authorization"] = self._token
        self._application_name = next((k for k, v in self.APP_ENDPOINT_MAP.items() if v(endpoint)), "")
        return super().request(method, endpoint, headers, params, data, body)


class CfApiClient(AppClient):
    """HTTP client for CF api calls. Uses token-based authentication."""

    _CF_API_CLIENT = None

    def __init__(self, platform_username, platform_password):
        super().__init__(platform_username, platform_password)

    @property
    def url(self):
        return "https://{}/v2/".format(config.get_config_value("cf_endpoint"))

    @classmethod
    def get_client(cls):
        if cls._CF_API_CLIENT is None:
            admin_username = config.TEST_SETTINGS["TEST_USERNAME"]
            admin_password = config.TEST_SETTINGS["TEST_PASSWORD"]
            cls._CF_API_CLIENT = cls(admin_username, admin_password)
        return cls._CF_API_CLIENT


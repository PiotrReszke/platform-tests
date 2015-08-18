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

import enum
import json
import random
import string
import time

from pyswagger import SwaggerApp
from pyswagger.core import BaseClient
import requests

from test_utils import config, get_logger, get_code_from_gmail


logger = get_logger("api client")


__all__ = ["UnexpectedResponseError", "AppClient", "ConsoleClient", "CfApiClient", "get_admin_client", "ClientRole"]


__ADMIN_CLIENT = None


def get_admin_client():
    global __ADMIN_CLIENT
    if __ADMIN_CLIENT is None:
        admin_username = config.TEST_SETTINGS["TEST_USERNAME"]
        admin_password = config.TEST_SETTINGS["TEST_PASSWORD"]
        client_type = config.TEST_SETTINGS["TEST_CLIENT_TYPE"]
        if client_type == "console":
            __ADMIN_CLIENT = ConsoleClient(admin_username, admin_password)
        elif client_type == "app":
            __ADMIN_CLIENT = AppClient(admin_username, admin_password)
    return __ADMIN_CLIENT


class UnexpectedResponseError(AssertionError):
    def __init__(self, status, error_message, message=None):
        message = message or "{} {}".format(status, error_message)
        super(UnexpectedResponseError, self).__init__(message)
        self.status = status
        self.error_message = error_message



class ClientRole(enum.Enum):
    undefined = "undefined"
    admin = "admin"
    org_manager = ("managers",)



class ApiClient(BaseClient):
    """Modeled after pyswagger Client"""

    __schemes__ = {'http', 'https'}
    _scheme = None

    def __init__(self, username, password):
        super().__init__()
        self._api_endpoint = None
        self._token = None
        self._username = username
        self._password = password
        self._domain = config.TEST_SETTINGS["TEST_ENVIRONMENT"]
        self._login_endpoint = config.CONFIG[self._domain]["login_endpoint"]
        self._session = requests.Session()
        if config.TEST_SETTINGS["TEST_DISABLE_SSL_VALIDATION"] is True:
            self._session.verify = False
        proxy = config.TEST_SETTINGS["TEST_PROXY"]
        if proxy is not None:
            self._session.proxies = {"https": proxy, "http": proxy}

    def request(self, req_and_resp, opt=None):
        opt = opt or {}
        swagger_request, swagger_response = super().request(req_and_resp, opt)
        swagger_request._SwaggerRequest__url = self._api_endpoint + swagger_request.path # fix hostname
        swagger_request.schemes[:] = [self._scheme]  # fix scheme
        # apply request-related options before preparation.
        swagger_request.prepare(scheme=self.prepare_schemes(swagger_request).pop(), handle_files=False)
        swagger_request._patch(opt)
        # if there are query parameters defined, but not passed, pyswagger passes None instead of omitting them
        fixed_query_params = {k: v for k, v in swagger_request.query if v != "None"}
        request = requests.Request(
            method=swagger_request.method.upper(),
            url=swagger_request.url,
            params=fixed_query_params,
            data=swagger_request.data,
            headers=swagger_request.header,
            files=self._prepare_uploaded_files(swagger_request)
        )
        if self._token is not None:
            swagger_request.header.update({"Authorization": self._token})
        request = self._session.prepare_request(request)
        self._log_request(request.method, request.url, request.headers, request.body)
        response = self._session.send(request)
        self._log_response(response.status_code, response.headers, response.text)
        swagger_response.apply_with(status=response.status_code, header=response.headers, raw=response.text)
        return swagger_response

    @staticmethod
    def _prepare_uploaded_files(swagger_request):
        file_obj = {}
        for k, v in swagger_request.files.items():
            f = v.data or open(v.filename, 'rb')
            if 'Content-Type' in v.header:
                file_obj[k] = (v.filename, f, v.header['Content-Type'])
            else:
                file_obj[k] = (v.filename, f)
        return file_obj

    def call(self, application_name, operation_id, **kwargs):
        app_schema_path = config.APP_SCHEMAS[application_name]
        app = SwaggerApp.create(app_schema_path)
        operation = app.op[operation_id](**kwargs)
        response = self.request(operation)
        if response.status // 100 != 2:
            error_message = response.data
            msg = "Unexpected response error: {0} '{1}'".format(response.status, response.raw)
            raise UnexpectedResponseError(status=response.status, error_message=error_message, message=msg)
        if "forgotPasswordLink" in response.raw:
            raise UnexpectedResponseError(response.status_code, response.text, "Client is not authorized")
        return response.data

    def file_download(self, method, url):
        local_filename = url.split('/')[-1]
        # NOTE the stream=True parameter
        r = requests.Request(method=method, url=url)
        r = self._session.prepare_request(r)
        response = self._session.send(r, stream=True)
        with open(local_filename, 'w+b') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
        return local_filename

    def _log_request(self, method, url, headers="", data="", params=None):
        if params:
            url = "{}?{}".format(url, "&".join(["{}={}".format(k, v) for k, v in params.items()]))
        # if "Authorization" in headers:
        #     headers["Authorization"] = "[SECRET]"
        if data is not None and "password" in data:
            data["password"] = "[SECRET]"
        msg = [
            "\n----------------Request------------------",
            "Client name: {}".format(self._username),
            "URL: {} {}".format(method, url),
            "Headers: {}".format(headers),
            "Content: {}".format(data),
            "-----------------------------------------\n"
        ]
        logger.debug("\n".join(msg))

    @staticmethod
    def _log_response(status, headers, text):
        msg = [
            "\n----------------Response------------------",
            "Status code: {}".format(status),
            "Headers: {}".format(headers),
            "Content: {}".format(text),
            "-----------------------------------------\n"
        ]
        logger.debug("\n".join(msg))


class ConsoleClient(ApiClient):
    _scheme = "https"

    def __init__(self, username, password=None):
        super().__init__(username, password)
        self._login_scheme = config.get_config_value("login.do_scheme")
        if password is None:
            self._username = username
            self._call_forgot_password()
            self._generate_password()
            code = self._get_reset_password_code(self._username)
            self._reset_password(code)
        else:
            self._authenticate()
        self._api_endpoint = "console.{}".format(config.CONFIG[self._domain]["api_endpoint"])

    def __repr__(self):
        return "ConsoleClient: {}".format(self._username)

    def _make_request(self, path, data="", headers="", params=None, method="POST"):
        request = requests.Request(method.upper(), path, data=data, headers=headers)
        request = self._session.prepare_request(request)
        self._log_request(method, path, headers, data)
        response = self._session.send(request)
        self._log_response(response.status_code, response.headers, response.text)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        if "forgotPasswordLink" in response.text:
            raise UnexpectedResponseError(response.status_code, response.text, "Client is not authorized")

    def _authenticate(self):
        logger.info("-------------------- Authenticating user {} --------------------".format(self._username))
        path = "{}://{}/login.do".format(self._login_scheme, self._login_endpoint)
        data = {"username": self._username, "password": self._password}
        headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        self._make_request(path, data, headers)

    def _call_forgot_password(self):
        logger.info("-------------------- Call forgot password for user {} --------------------".format(self._username))
        path = "{}://{}/forgot_password.do".format(self._login_scheme, self._login_endpoint)
        data = {"email": self._username}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self._make_request(path, data, headers)

    def _reset_password(self, code):
        logger.info("-------------------- Reset password for user {} --------------------".format(self._username))
        path = "{}://{}/reset_password.do".format(self._login_scheme, self._login_endpoint)
        data = {"email": self._username, "password": self._password, "password_confirmation": self._password,
                "code": code}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self._make_request(path, data, headers)

    def _generate_password(self):
        pass_length = 8
        base = string.ascii_letters + string.digits + "%"
        self._password = ["".join(random.choice(base)) for _ in range(pass_length)]

    @staticmethod
    def _get_reset_password_code(username):
        return get_code_from_gmail(username)


class AppClient(ApiClient):

    TOKEN_EXPIRY_TIME = 298  # (in seconds) 5 minutes minus 2s buffer
    _scheme = "http"

    def __init__(self, username, password):
        super().__init__(username, password)
        self._token_retrieval_time = 0
        self._get_token()

    def __repr__(self):
        return "AppClient: {}".format(self._username)

    def _get_token(self):
        logger.info("-------------------- Retrieve token for user {} --------------------".format(self._username))
        path = "https://{}/oauth/token".format(self._login_endpoint)
        headers = {
            "Authorization": config.TEST_SETTINGS["TEST_LOGIN_TOKEN"],
            "Accept": "application/json"
        }
        data = {"username": self._username, "password": self._password, "grant_type": "password"}
        request = requests.Request("POST", path, data=data, headers=headers)
        self._token_retrieval_time = time.time()
        response = self._session.send(request.prepare())
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        self._token = "Bearer {}".format(json.loads(response.text)["access_token"])

    def call(self, application_name, operation_id, **kwargs):
        self._api_endpoint = "{}.{}".format(application_name, config.CONFIG[self._domain]["api_endpoint"])
        # check that token has not expired
        if (self._token is not None) and (time.time() - self._token_retrieval_time > self.TOKEN_EXPIRY_TIME):
            self._get_token()
        return super().call(application_name, operation_id, **kwargs)


class CfApiClient(AppClient):

    _ME = None

    def __init__(self):
        username = config.TEST_SETTINGS["TEST_USERNAME"]
        password = config.TEST_SETTINGS["TEST_PASSWORD"]
        super().__init__(username, password)
        self._api_endpoint = "http://{}/v2/".format(config.get_config_value("cf_endpoint"))

    @classmethod
    def get_client(cls):
        if cls._ME is None:
            cls._ME = cls()
        return cls._ME

    def call(self, method, path, params=None, body=None):
        if (time.time() - self._token_retrieval_time) > self.TOKEN_EXPIRY_TIME:
            self._get_token()
        request = requests.Request(
            method=method.upper(),
            params=params,
            url=self._api_endpoint + path,
            headers={"Accept": "application/json", "Authorization": self._token},
            json=body
        )
        request = request.prepare()
        self._log_request(method=request.method, url=request.url, headers=request.headers, data=body)
        response = self._session.send(request)
        self._log_response(status=response.status_code, headers=response.headers, text=response.text)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        if response.text == "":
            return response.text
        return json.loads(response.text)

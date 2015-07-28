import json
from math import floor, ceil
import random
import string
import time

from pyswagger import SwaggerApp
from pyswagger.core import BaseClient
import requests

from test_utils.gmail_api import get_code_from_gmail
from test_utils.logger import get_logger
from test_utils import config


logger = get_logger("api client")


__all__ = ["UnexpectedResponseError", "AppClient", "ConsoleClient", "CfApiClient"]


class UnexpectedResponseError(Exception):
    def __init__(self, status, error_message, message=None):
        message = message or "{} {}".format(status, error_message)
        super(UnexpectedResponseError, self).__init__(message)
        self.status = status
        self.error_message = error_message


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
        response = self._session.send(request)
        self._log_request(request.method, request.url, request.headers, request.body, fixed_query_params)
        swagger_response.apply_with(status=response.status_code, header=response.headers, raw=response.text)
        self._log_response(swagger_response.status, swagger_response.header, swagger_response.raw)
        return swagger_response

    def _prepare_uploaded_files(self, swagger_request):
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
        return response.data

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
        self._log_request(method, path, headers, data, params)
        response = self._session.send(request)
        self._log_response(response.status_code, response.headers, response.text)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        if "forgotPasswordLink" in response.text:
            raise UnexpectedResponseError(response.status_code, response.text, "Client is not authorized")

    def _authenticate(self):
        logger.info("-------------------- Authenticating user {} --------------------".format(self._username))
        path = "{}://{}/login.do".format(config.get_config_value("login.do_scheme"), self._login_endpoint)
        data = {"username": self._username, "password": self._password}
        headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        self._make_request(path, data, headers)

    def _call_forgot_password(self):
        logger.info("-------------------- Call forgot password for user {} --------------------".format(self._username))
        path = "https://{}/forgot_password.do".format(self._login_endpoint)
        data = {"email": self._username}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self._make_request(path, data, headers)

    def _reset_password(self, code):
        logger.info("-------------------- Reset password for user {} --------------------".format(self._username))
        path = "https://{}/reset_password.do".format(self._login_endpoint)
        data = {"email": self._username, "password": self._password, "password_confirmation": self._password,
                "code": code}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self._make_request(path, data, headers)

    def _generate_password(self):
        pass_length = 8
        letters = ''.join(random.choice(string.ascii_letters) for _ in range(ceil(pass_length / 2)))
        digits = ''.join(random.choice(string.digits) for _ in range(floor(pass_length / 2) - 1))
        p = letters + digits + '%'
        self._password = p

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
        self._log_request(method=request.method, url=request.url, headers=request.headers)
        response = self._session.send(request)
        self._log_response(status=response.status_code, headers=response.headers, text=response.text)
        if not response.ok:
            raise UnexpectedResponseError(response.status_code, response.text)
        return json.loads(response.text)

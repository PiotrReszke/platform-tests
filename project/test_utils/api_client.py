import json
import os

from pyswagger import SwaggerApp
from pyswagger.core import BaseClient
from requests import Session, Request

from test_utils.logger import get_logger


logger = get_logger("api client")


class Client(BaseClient):
    """Modeled after pyswagger Client"""

    __schemes__ = {'http', 'https'}
    PROXIES = {
        "https": "proxy-mu.intel.com:911",
        "http": "proxy-mu.intel.com:911"
    }

    def __init__(self, scheme, hostname, authorization_token=None):
        super(Client, self).__init__()
        self.__s = Session()
        # self.__s.verify = False
        self._host = hostname
        self._scheme = scheme
        self._auth_token = authorization_token

    def request(self, req_and_resp, opt=None):
        opt = {} if opt is None else opt

        sw_request, sw_response = super(Client, self).request(req_and_resp, opt)

        self.fix_hostname(sw_request)
        sw_request.schemes[:] = [self._scheme] # fix scheme

        # apply request-related options before preparation.
        sw_request.prepare(scheme=self.prepare_schemes(sw_request).pop(), handle_files=False)
        sw_request._patch(opt)

        # prepare for uploaded files
        file_obj = {}
        for k, v in sw_request.files.items():
            f = v.data or open(v.filename, 'rb')
            if 'Content-Type' in v.header:
                file_obj[k] = (v.filename, f, v.header['Content-Type'])
            else:
                file_obj[k] = (v.filename, f)

        # if there are query parameters defined, but not passed, pyswagger passes None instead of omitting them
        fixed_query_params = {k: v for k, v in sw_request.query if v != 'None'}
        request = Request(
            method=sw_request.method.upper(),
            url=sw_request.url,
            params=fixed_query_params,
            data=sw_request.data,
            headers=sw_request.header,
            files=file_obj
        )
        if self._auth_token is not None:
            sw_request.header.update({"Authorization": self._auth_token})
        request = self.__s.prepare_request(request)
        self.__s.proxies = self.PROXIES
        response = self.__s.send(request)
        self.__log_request(request.method, request.url, request.headers, request.body)
        sw_response.apply_with(status=response.status_code, header=response.headers, raw=response.text)
        self.__log_response(sw_response.status, sw_response.header, sw_response.raw)
        return sw_response

    def fix_hostname(self, request):
        # modify private property
        request._SwaggerRequest__url = self._host + request.path

    def __log_request(self, method, url, headers="", data="", params=None):
        if params is not None:
            url += "?" + "&".join(["%s=%s" % (k, v) for k, v in params.items()])
        msg = [
            "\n----------------Request------------------",
            "URL: " + method + " " + str(url),
            "Headers: " + str(headers),
            "Content: " + str(data),
            "-----------------------------------------\n"
        ]
        logger.debug("\n".join(msg))

    def __log_response(self, status, headers, text):
        msg = [
            "\n----------------Response------------------",
            "Status code: " + str(status),
            "Headers: " + str(headers),
            "Content: " + text,
            "-----------------------------------------\n"
        ]
        logger.debug("\n".join(msg))


class UnexpectedResponseError(Exception):
    def __init__(self, status, error_message, message=None):
        super(UnexpectedResponseError, self).__init__(message)
        self.status = status
        self.error_message = error_message


class ApiClient(object):

    API_SCHEMA_PATH = "swagger/user_management_swagger.json"
    LOGIN_SCHEMA_PATH = "swagger/login_swagger.json"
    LOGIN_TOKEN = "Basic Y2Y6"

    def __init__(self, application):
        self._application = application
        self._domain = os.environ["TEST_ENVIRONMENT"]
        username = os.environ["TEST_USERNAME"]
        password = os.environ["TEST_PASSWORD"]
        self._token = self.get_token(username, password)
        self._app = SwaggerApp.create(self.API_SCHEMA_PATH)
        self._client = Client(*self.api_endpoint, authorization_token=self._token)

    @property
    def login_endpoint(self):
        return ("https", "login.run.{}".format(self._domain))

    @property
    def api_endpoint(self):
        return ("http", "{}.apps.{}".format(self._application, self._domain))

    def get_token(self, username, password):
        logger.info("-------------------- Retrieve token for user {} --------------------".format(username))
        self._app = SwaggerApp.create(self.LOGIN_SCHEMA_PATH)
        self._client = Client(*self.login_endpoint, authorization_token=self.LOGIN_TOKEN)
        response = self.call("get_token", username=username, password=password)
        return "Bearer {}".format(response["access_token"])

    def call(self, operation_id, **kwargs):
        operation = self._app.op[operation_id](**kwargs)
        expected_responses = (operation)[1]._SwaggerResponse__op._Operation__responses
        response = self._client.request(operation)
        if response.status/100 != 2 or (str(response.status) not in expected_responses):
            error_message = response.data
            msg = "Unexpected response: {0} '{1}', expected: {2}".format(response.status, response.raw,
                                                                         ",".join(expected_responses.keys()))
            raise UnexpectedResponseError(status=response.status, error_message=error_message, message=msg)
        else:
            return response.data

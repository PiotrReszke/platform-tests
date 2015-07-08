import time

from pyswagger import SwaggerApp
from pyswagger.core import BaseClient
from requests import Session, Request

from test_utils.logger import get_logger
import test_utils.config as config


logger = get_logger("api client")


class Client(BaseClient):
    """Modeled after pyswagger Client"""

    __schemes__ = {'http', 'https'}

    def __init__(self, scheme, hostname, authorization_token=None, proxy=None, obscure_from_log=None):
        """In obscure_logged_data pass an iterable containing strings which are to be obscured from logs"""
        super(Client, self).__init__()
        self._obscure_from_log = [] if obscure_from_log is None else obscure_from_log
        self.__s = Session()
        # self.__s.verify = False
        self._host = hostname
        self._scheme = scheme
        self._auth_token = authorization_token
        self._proxies = {"https": proxy, "http": proxy} if proxy is not None else proxy

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
        self.__s.proxies = self._proxies
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
        for s in self._obscure_from_log:
            data = data.replace(s, "[SECRET]")
        if "Authorization" in headers:
            headers["Authorization"] = "[SECRET]"
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

    LOGIN_SCHEMA_PATH = "swagger/login_swagger.json"
    TOKEN = None
    TOKEN_RETRIEVAL_TIME = 0
    TOKEN_EXPIRY_TIME = 298 # (in seconds) 5 minutes minus 2s buffer

    def __init__(self, application_name):
        self._application = application_name
        self._domain = config.TEST_SETTINGS["TEST_ENVIRONMENT"]
        self._proxy = config.TEST_SETTINGS["TEST_PROXY"]
        self._username = config.TEST_SETTINGS["TEST_USERNAME"]
        self._password = config.TEST_SETTINGS["TEST_PASSWORD"]
        self._get_token()
        api_schema = config.APP_SCHEMAS[application_name]
        self._app = SwaggerApp.create(api_schema)
        self._client = Client(*self.api_endpoint, authorization_token=self.TOKEN, proxy=self._proxy)

    @property
    def api_endpoint(self):
        path = "{}.{}".format(self._application, config.CONFIG[self._domain]["api_endpoint"])
        return ("http", path)

    @property
    def login_endpoint(self):
        return ("https", config.CONFIG[self._domain]["login_endpoint"])

    def _get_token(self):
        logger.info("-------------------- Retrieve token for user {} --------------------".format(self._username))
        login_token = config.TEST_SETTINGS["TEST_LOGIN_TOKEN"]
        app = SwaggerApp.create(self.LOGIN_SCHEMA_PATH)
        client = Client(*self.login_endpoint, authorization_token=login_token, proxy=self._proxy, obscure_from_log=[self._password])
        operation = app.op["get_token"](username=self._username, password=self._password)
        response = client.request(operation)
        self.TOKEN_RETRIEVAL_TIME = time.time()
        self._verify_response_status(operation, response)
        self.TOKEN = "Bearer {}".format(response.data["access_token"])

    def switch_user(self, username, password):
        self._username = username
        self._password = password
        self._get_token()

    def _verify_response_status(self, operation, response):
        expected_responses = (operation)[1]._SwaggerResponse__op._Operation__responses
        if response.status/100 != 2 or (str(response.status) not in expected_responses):
            error_message = response.data
            msg = "Unexpected response: {0} '{1}', expected: {2}".format(response.status, response.raw,
                                                                         ",".join(expected_responses.keys()))
            raise UnexpectedResponseError(status=response.status, error_message=error_message, message=msg)

    def call(self, operation_id, **kwargs):
        # check that token has not expired
        now = time.time()
        if now - self.TOKEN_RETRIEVAL_TIME > self.TOKEN_EXPIRY_TIME:
            self._get_token()
        operation = self._app.op[operation_id](**kwargs)
        response = self._client.request(operation)
        self._verify_response_status(operation, response)
        return response.data


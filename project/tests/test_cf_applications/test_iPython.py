import unittest

from test_utils import ApiTestCase, UnexpectedResponseError, get_logger, config
from test_utils.objects import Application, Organization, ServiceInstance, ServiceType


logger = get_logger("iPython test")


@unittest.skipIf(config.TEST_SETTINGS["TEST_ENVIRONMENT"] == "gotapaas.eu", "No iPython on gotapaas.eu")
class iPythonConsoleTest(ApiTestCase):

    PROXY_NAME = "ipython-proxy"
    SERVICE_NAME = "ipython"
    IPYTHON_PORT = 4443

    def setUp(self):
        self.test_org = Organization.create(space_names=("test-space",))
        self.test_space = self.test_org.spaces[0]

    def test_deploy_iPython_console_instance(self):
        """Check deployment of iPython console instance and login to Jupyter"""

        marketplace = ServiceType.api_get_list_from_marketplace(space_guid=self.test_space.guid)
        ipython_service = next((st for st in marketplace if st.label == self.PROXY_NAME), None)
        self.assertIsNotNone(ipython_service, "{} service was not found in marketplace".format(self.PROXY_NAME))

        try:
            ServiceInstance.api_create(
                name="iPython-test-{}".format(self.get_timestamp()),
                service_plan_guid=ipython_service.service_plan_guids[0],
                service_type_guid=ipython_service.guid,
                space_guid=self.test_space.guid
            )
        except UnexpectedResponseError as e:
            if e.status == 500 and "Read timed out" in e.error_message:
                logger.info("This is an expected read timeout")
            else:
                raise

        # check that there is 1 iPython application - within timeout
        self.assertLenEqualWithinTimeout(
            timeout=120,
            expected_len=1,
            callableObj=Application.api_get_list,
            space_guid=self.test_space.guid,
            service_label=self.SERVICE_NAME
        )

        ipython_app = Application.api_get_list(space_guid=self.test_space.guid, service_label=self.SERVICE_NAME)[0]
        self.assertTrue(ipython_app.is_started, "The {} app is not started".format(ipython_app.name))

        # iPython Jupyter login
        password = ipython_app.cf_api_env()["VCAP_SERVICES"][self.SERVICE_NAME][0]["credentials"]["password"]
        url = "{}:{}".format(ipython_app.urls[0], self.IPYTHON_PORT)
        # although the application is created, actual iPython takes longer to start - hence timeout
        response = self.exec_within_timeout(120, ipython_app.application_api_request, method="POST", scheme="https",
                                            url=url, endpoint="login", params={"next": "/tree"},
                                            data={"password": password})
        self.assertTrue("Logout" in response, "Could not log into Jupyter. Response:\n{}".format(response))


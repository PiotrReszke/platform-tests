import os
import re
import shutil

from test_utils import ApiTestCase, cleanup_after_failed_setup, get_logger
from test_utils.objects import Organization, Space, Transfer, DataSet
from test_utils.cli.cf_service import CfBroker, CfService
from test_utils.cli.venv import Virtualenv
import test_utils.cli.cloud_foundry as cf

logger = get_logger("test transfer")


class TestCreateAtkInstance(ApiTestCase):

    DATA_SOURCE = Transfer.get_test_transfer_link()
    UAA_FILENAME = "pyclient.test"
    UAA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "atk_python2", UAA_FILENAME)
    ATK_TEST_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "atk_python2", "atk_python_client")
    ATK_CLIENT_INDEX_URL = "http://host.gao.intel.com/pypi/master/simple"
    TRUSTED_HOST = "host.gao.intel.com"
    ATK_CLIENT_NAME = "trustedanalytics"

    @classmethod
    def tearDownClass(cls):
        Organization.api_delete_test_orgs()
        try:
            os.remove(cls.UAA_FILE_PATH)
        except OSError:
            pass

    def test_create_atk_instance(self):
        org = Organization.create(space_names=("test_space",))
        org.add_admin()
        space = org.spaces[0]
        space.add_admin(org.guid)

        transfer = Transfer.api_create(source=self.DATA_SOURCE, org_guid=org.guid)
        transfer.ensure_finished()
        transfers = Transfer.api_get_list(orgs=[org])
        self.assertInList(transfer, transfers)
        dataset = DataSet.api_get_matching_to_transfer(org_list=[org], transfer=transfer)
        dataset.publish_in_hive()

        cf.cf_login(org.name, space.name)
        broker = CfBroker("atk")
        CfBroker.cf_service_target(org.name, space.name)  # without it service can be created in any space
        expected_atk_service = CfService.cf_create_instance(broker_name=broker.name, plan=broker.plan)
        service_list = CfService.cf_get_list()
        expected_atk_service.add_URL_and_generated_name_via_space(space=space.guid)
        self.assertInList(expected_atk_service, service_list)

        atk_vitualenv = Virtualenv("atk_virtualenv")
        atk_response = 0
        try:
            atk_vitualenv.create()
            atk_vitualenv.pip_install(self.ATK_CLIENT_NAME, extra_index_url=self.ATK_CLIENT_INDEX_URL,
                                      trusted_host=self.TRUSTED_HOST)
            atk_response = atk_vitualenv.run_atk_script(self.ATK_TEST_SCRIPT_PATH,
                                         arguments={
                                             "--organization": org.name,
                                             "--atk": expected_atk_service.URL,
                                             "--transfer": transfer.title,
                                             "--uaa_file_name": self.UAA_FILENAME
                                         })
        except:
            atk_vitualenv.delete()


        if atk_response == 0:
            raise Exception("ATK script has not run properly")
        elif atk_response == 1:
            raise Exception("Python client failed to connect to ATK instance")
        elif atk_response == 2:
            raise Exception("Hive could not find resources")

        with open(self.UAA_FILE_PATH) as f:
            content = f.read()
        self.assertNotEqual(content, "")

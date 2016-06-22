from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import ServiceInstance
from configuration import config
import requests
import re

class Seahorse(TapTestCase):
    seahorse_label = "k-seahorse-dev"
    tap_domain = config.CONFIG["domain"]
    username = config.CONFIG["admin_username"]
    password = config.CONFIG["admin_password"]

    def create_session(self, instance_url, domain, login, password):
        session = requests.Session()
        login_form = session.get(instance_url, verify=False)

        print("LOGIN_FORM")
        print(login_form.text)
        print(login_form)
        csrf_value_regex = r"x-uaa-csrf.*value=\"(.*)\""
        match = re.search(csrf_value_regex, login_form.text, re.IGNORECASE)
        csrf_value = match.group(1)
        print("CSRF {0}".format(csrf_value))
        payload = {'username': login, 'password': password, 'X-Uaa-Csrf': csrf_value}
        session.post(url='http://login.{0}/login.do'.format(domain), data=payload)
        return session

    def test_create_instance_in_seahorse_org(self):
        test_org_uuid = '3761da19-692c-4afb-95b6-f20d2d37ec3f'
        test_space_uuid = 'b641e43e-b89b-4f32-b360-f1cf6bd1aa74'

        service_instance = ServiceInstance.api_create_with_plan_name(
            test_org_uuid, test_space_uuid, self.seahorse_label, service_plan_name="free")

        service_instance.ensure_created()
        seahorse_url="https://"+service_instance.name + service_instance.guid + "." + self.tap_domain
        print(seahorse_url)
        session=self.create_session(seahorse_url, domain=self.tap_domain, login=self.username, password=self.password)

        resp=session.get(seahorse_url + '/v1/workflows')
        print(resp.text)
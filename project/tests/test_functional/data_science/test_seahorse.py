from modules.runner.tap_test_case import TapTestCase
from modules.tap_object_model import ServiceType, ServiceInstance, Organization, Space
from configuration import config
import requests
import sys
import re

class Seahorse(TapTestCase):
    seahorse_label = "k-seahorse-dev"
    tap_domain = config.CONFIG["domain"]

    def create_session(self, instance_url, domain, login, password):
        session = requests.Session()
        login_form = session.get(instance_url, verify=False)
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

        service_instance = ServiceInstance.api_create(test_org_uuid, test_space_uuid, self.seahorse_label,
                                                      service_plan_name="free")

        #seahorse_url = "https://"+service_instance.name + service_instance.guid + "." + self.tap_domain
        #print(seahorse_url)

        seahorse_url="https://pr_20160622_114623_851399-ca4a4be1-7cbd-4995-8725-308745b06a6c.seahorse-krb.gotapaas.eu/"
        session=self.create_session(seahorse_url, domain=self.tap_domain, login="somelogin", password="somepass")

        resp=session.get(seahorse_url + '/v1/workflows')
        print(resp.text)

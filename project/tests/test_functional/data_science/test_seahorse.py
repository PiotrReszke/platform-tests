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

        service_instance = ServiceInstance.api_create_with_plan_name(test_org_uuid, test_space_uuid, self.seahorse_label,
                                                      service_plan_name="free")

        #seahorse_url = "https://"+service_instance.name + service_instance.guid + "." + self.tap_domain
        #print(seahorse_url)

        seahorse_url="https://pr_20160622_114623_851399-ca4a4be1-7cbd-4995-8725-308745b06a6c.seahorse-krb.gotapaas.eu/"
        session=self.create_session(seahorse_url, domain=self.tap_domain, login=self.username, password=self.password)

        resp=session.get(seahorse_url + '/v1/workflows')
        print(resp.text)

#{"ajk-test":{"guid":"c6078b05-491d-46a0-808f-8b500148b400","hostname":"ajk_test-c6078b05-491d-46a0-808f-8b500148b400.seahorse-krb.gotapaas.eu","login":"","password":""},"pr_20160622_120229_669492":{"guid":"9d05a0d5-8951-4283-9d7e-21b966fcc39c","hostname":"pr_20160622_120229_669492-9d05a0d5-8951-4283-9d7e-21b966fcc39c.seahorse-krb.gotapaas.eu","login":"","password":""},"test":{"guid":"c1d26a50-d20a-40d6-aba4-342123b1e75a","hostname":"test-c1d26a50-d20a-40d6-aba4-342123b1e75a.seahorse-krb.gotapaas.eu","login":"","password":""},"xyz":{"guid":"8eff882a-649d-4333-bb27-bbb20ff6b80b","hostname":"xyz-8eff882a-649d-4333-bb27-bbb20ff6b80b.seahorse-krb.gotapaas.eu","login":"","password":""},"piotr_test":{"guid":"c81c884c-2a29-44c6-b0ee-809fd5c61ad8","hostname":"piotr_test-c81c884c-2a29-44c6-b0ee-809fd5c61ad8.seahorse-krb.gotapaas.eu","login":"","password":""},"pr_20160622_114329_754114":{"guid":"681e29e5-2e78-4b9a-bd98-683710a1ff93","hostname":"pr_20160622_114329_754114-681e29e5-2e78-4b9a-bd98-683710a1ff93.seahorse-krb.gotapaas.eu","login":"","password":""},"pr_20160622_114142_861305":{"guid":"cef91405-32b0-4dd3-81ba-49224c538716","hostname":"pr_20160622_114142_861305-cef91405-32b0-4dd3-81ba-49224c538716.seahorse-krb.gotapaas.eu","login":"","password":""}}
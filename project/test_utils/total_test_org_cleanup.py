import re

from test_utils.objects import Organization
import test_utils.cli.cloud_foundry as cf_cli


# TEST_ORG_PATTERN = '^test_org_[0-9]{8}'
TEST_ORG_PATTERN = "^test_org_[0-9]{8}_[0-9]{6}_[0-9]{6}$"
# TEST_ORG_PATTERN = 'testorg[0-9]{6}'

if __name__ == "__main__":

    ORG_NAME = "seedorg"
    SPACE_NAME = "seedspace"

    cf_cli.cf_login(ORG_NAME, SPACE_NAME)
    all_orgs = Organization.get_list()
    test_orgs = [o for o in all_orgs if re.match(TEST_ORG_PATTERN, o.name)]
    for org in test_orgs:
        org.delete()

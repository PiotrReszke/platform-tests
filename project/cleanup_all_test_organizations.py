import re

from test_utils import get_logger
from test_utils.objects import Organization


TEST_ORG_PATTERN = "^test_org_[0-9]{8}_[0-9]{6}_[0-9]{6}$"
logger = get_logger("organization cleanup")


if __name__ == "__main__":

    all_orgs = Organization.get_list()
    test_orgs = [o for o in all_orgs if re.match(TEST_ORG_PATTERN, o.name)]
    logger.info("Deleting {} organizations: {}".format(len(test_orgs), test_orgs))
    failed_to_delete = []
    for org in test_orgs:
        try:
            org.api_delete(with_spaces=True)
        except Exception as e:
            failed_to_delete.append(org)
            logger.error("Could not delete {}\n{}\n".format(org, e))

    logger.info("Deleted {} orgs. Could not delete {}: {}".format(
        len(test_orgs) - len(failed_to_delete), len(failed_to_delete), failed_to_delete
    ))

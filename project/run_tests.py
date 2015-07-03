import argparse
import unittest

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from test_utils import get_logger
from test_utils.config import CONFIG


logger = get_logger("run tests")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Platform API Automated Tests")
    parser.add_argument("-e",
                        "--environment",
                        default=CONFIG["DEFAULT_SETTINGS"]["TEST_ENVIRONMENT"],
                        help="environment where tests are to be run, e.g. gotapaas.com")
    parser.add_argument("-u",
                        "--username",
                        default=CONFIG["DEFAULT_SETTINGS"]["TEST_USERNAME"],
                        help="username for logging into Cloud Foundry")
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_arguments()
    CONFIG["TEST_SETTINGS"]["TEST_ENVIRONMENT"] = args.environment
    logger.info("[TEST_ENVIRONMENT={}]".format(CONFIG["TEST_SETTINGS"]["TEST_ENVIRONMENT"]))
    CONFIG["TEST_SETTINGS"]["TEST_USERNAME"] = args.username
    logger.info("[TEST_USERNAME={}]".format(CONFIG["TEST_SETTINGS"]["TEST_USERNAME"]))

    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestSuite(unittest.TestLoader().loadTestsFromName("tests.test_organization"))
    runner.run(suite)

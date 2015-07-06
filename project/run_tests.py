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
    parser.add_argument("-p",
                        "--proxy",
                        default="",
                        help="set proxy for api client")
    return parser.parse_args()


def set_config(args):
    CONFIG["TEST_SETTINGS"]["TEST_ENVIRONMENT"] = args.environment
    logger.info("[TEST_ENVIRONMENT={}]".format(CONFIG["TEST_SETTINGS"]["TEST_ENVIRONMENT"]))
    CONFIG["TEST_SETTINGS"]["TEST_USERNAME"] = args.username
    logger.info("[TEST_USERNAME={}]".format(CONFIG["TEST_SETTINGS"]["TEST_USERNAME"]))
    CONFIG["TEST_SETTINGS"]["proxy"] = args.proxy
    if args.proxy != "":
        logger.info("[using {}]".format(args.proxy))
    else:
        logger.info("[no proxy]")


if __name__ == "__main__":

    args = parse_arguments()
    set_config(args)

    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner(verbosity=3)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.discover("tests"))
    runner.run(suite)

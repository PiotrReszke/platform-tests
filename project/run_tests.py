import argparse
import os
import unittest

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from test_utils import get_logger


logger = get_logger("run tests")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Platform API Automated Tests")
    parser.add_argument("-e",
                        "--environment",
                        default="gotapaas.eu",
                        help="environment where tests are to be run, e.g. demo-gotapaas.com")
    parser.add_argument("-u",
                        "--username",
                        default="admin",
                        help="username for logging into Cloud Foundry")
    parser.add_argument("-p",
                        "--password",
                        default="c1oudc0w",
                        help="password for logging into Cloud Foundry")
    return parser.parse_args()


def set_environment_variable(name, value, secret=False):
    """Set environment variable, logging the key and value. If secret is True, the value will be obscured."""
    os.environ[name] = value
    if secret:
        value = "*" * len(value)
    logger.info("[{0}={1}]".format(name, value))


if __name__ == "__main__":
    args = parse_arguments()
    set_environment_variable("TEST_ENVIRONMENT", args.environment)
    set_environment_variable("TEST_USERNAME", args.username)
    set_environment_variable("TEST_PASSWORD", args.password, secret=True)

    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner(verbosity=3)
    suite = unittest.TestSuite(unittest.TestLoader().loadTestsFromName("tests.test_organization"))
    runner.run(suite)

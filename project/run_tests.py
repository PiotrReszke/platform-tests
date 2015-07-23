import os
import unittest

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from test_utils.logger import get_logger
from test_utils import config



logger = get_logger("run tests")



if __name__ == "__main__":

    # parse settings passed from command line
    args = config.parse_arguments()

    config.update_test_settings(client_type=args.client_type,
                                test_environment=args.environment,
                                test_username=args.username,
                                proxy=args.proxy,
                                password=args.password,
                                login_token=args.login_token,
                                github_auth=(args.github_username, args.github_password))

    if args.test is None:
        test_dir = "tests"
    else:
        test_dir = args.test
        if os.path.exists("tests/" + test_dir):
            test_dir = "tests/" + test_dir
        else:
            raise NotADirectoryError('Directory {} doesn\'t exists'.format(test_dir))

    # run tests
    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner(verbosity=3)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.discover(test_dir))
    runner.run(suite)

import unittest

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from test_utils import get_logger
import test_utils.config as config


logger = get_logger("run tests")



if __name__ == "__main__":

    # parse settings passed from command line
    args = config.parse_arguments()
    config.update_test_settings(test_environment=args.environment,
                                test_username=args.username,
                                proxy=args.proxy,
                                password=args.password,
                                login_token=args.login_token)


    # run tests
    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner(verbosity=3)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.discover("tests"))
    runner.run(suite)

import unittest
import sys
import os
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

    if not '--test' in sys.argv:
        test_dir = "tests/"
    else:
        #testindex = sys.argv.index('--test')
        #test_dir = sys.argv[testindex+1]
        test_dir=args.test
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

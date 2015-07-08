import unittest

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

from test_utils import get_logger


logger = get_logger("run tests")



if __name__ == "__main__":

    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner(verbosity=3)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.discover("tests"))
    runner.run(suite)

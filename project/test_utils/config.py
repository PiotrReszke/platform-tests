import os

from configobj import ConfigObj

CONFIG = ConfigObj("test_utils/config.ini")


# The unctions below serve as a workaround to allow running tests both from command line, and using PyCharm's Unittest runner


def get_config_value(key):
    value = CONFIG["TEST_SETTINGS"].get(key)
    if value is None:
        value = os.environ.get(key)
    return value

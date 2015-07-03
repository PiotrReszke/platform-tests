import configparser
import os


CONFIG = configparser.ConfigParser()
CONFIG.read("test_utils/config.ini")
SECRET = configparser.ConfigParser()
SECRET.read("test_utils/.secret.ini")


def get_password(environment, username):
    try:
        return SECRET[environment][username]
    except KeyError:
        raise KeyError("Password for {} on {} is not specified.".format(username, environment))


def get_login_token(environment):
    return SECRET[environment]["login_token"]


def get_schema_path(app_name):
    try:
        return CONFIG["APP_SCHEMAS"][app_name]
    except KeyError:
        raise KeyError("Schema path for {} is not defined".format(app_name))


# workaround to allow running tests both from command line, and using PyCharm's Unittest runner
def get_test_setting(key):
    if key in ["TEST_ENVIRONMENT", "TEST_USERNAME"]:
        value = CONFIG["TEST_SETTINGS"].get(key)
        if value is None:
            value = os.environ.get("TEST_ENVIRONMENT")
        return value


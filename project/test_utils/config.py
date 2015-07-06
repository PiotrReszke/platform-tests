import configparser
import os


CONFIG = configparser.ConfigParser()
CONFIG.read("test_utils/config.ini")
SECRET = configparser.ConfigParser()
SECRET.read("test_utils/.secret.ini")


def get_password(environment, username):
    settings_password = CONFIG["TEST_SETTINGS"].get("TEST_PASSWORD")
    if settings_password is not None:
        return settings_password
    else:
        try:
            return SECRET[environment][username]
        except KeyError:
            raise KeyError("Password for {} on {} is not specified.".format(username, environment))


def get_login_token(environment):
    settings_token = CONFIG["TEST_SETTINGS"].get("LOGIN_TOKEN")
    if settings_token is not None:
        return settings_token
    else:
        return SECRET[environment]["login_token"]


def get_schema_path(app_name):
    try:
        return CONFIG["APP_SCHEMAS"][app_name]
    except KeyError:
        raise KeyError("Schema path for {} is not defined".format(app_name))


def get_proxy():
    proxy = CONFIG["TEST_SETTINGS"]["proxy"]
    if proxy != "":
        return proxy


# workaround to allow running tests both from command line, and using PyCharm's Unittest runner
def get_test_setting(key):
    if key in ["TEST_ENVIRONMENT", "TEST_USERNAME"]:
        value = CONFIG["TEST_SETTINGS"].get(key)
        if value is None:
            value = os.environ.get(key)
        return value



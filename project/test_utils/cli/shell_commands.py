import subprocess

from test_utils import get_logger


logger = get_logger("shell_commands")


def log_command(command, replace=()):
    logger.info("Execute {}".format(" ".join(command)).replace(replace))


def cd(path):
    command = [cd, path]
    log_command(command)
    subprocess.call(command)

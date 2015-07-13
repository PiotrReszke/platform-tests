import subprocess

from test_utils import get_logger


logger = get_logger("shell_commands")


def log_command(command, replace=None):
    msg = "Execute {}".format(" ".join(command))
    if replace is not None:
        msg = msg.replace(*replace)
    logger.info(msg)


def cd(path):
    command = [cd, path]
    log_command(command)
    subprocess.call(command)

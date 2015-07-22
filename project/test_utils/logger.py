import logging
import sys


__all__ = ["get_logger", "log_command"]


format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
logging.basicConfig(stream=sys.stdout, format=format, level=logging.DEBUG)
logging.getLogger("pyswagger.core").setLevel(logging.WARNING)
logging.getLogger("pyswagger.getter").setLevel(logging.WARNING)
logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("paramiko.transport").setLevel(logging.WARNING)



def get_logger(name):
    return logging.getLogger(name)


def log_command(command, replace=None):
    logger = get_logger("shell command")
    msg = "Execute {}".format(" ".join(command))
    if replace is not None:
        msg = msg.replace(*replace)
    logger.info(msg)
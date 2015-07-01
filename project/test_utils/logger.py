import logging
import sys


format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
logging.basicConfig(stream=sys.stdout, format=format, level=logging.DEBUG)
logging.getLogger("pyswagger.core").setLevel(logging.WARNING)
logging.getLogger("pyswagger.getter").setLevel(logging.WARNING)
logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.WARNING)



def get_logger(name):
    return logging.getLogger(name)
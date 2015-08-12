import os
import shutil
import subprocess

from git import Repo
from test_utils import config


def clone_repository(repository_name, target_directory, owner="intel-data"):
    API_URL = "https://{}:{}@github.com/{}/{}.git".format(config.get_github_username(), config.get_github_password(), owner, repository_name)
    if os.path.exists(target_directory):
        shutil.rmtree(target_directory)
    os.mkdir(target_directory)
    Repo.clone_from(API_URL, target_directory)


def compile_mvn(directory):
    current_path = os.getcwd()
    os.chdir(directory)
    subprocess.call(["mvn", "clean", "package"])
    os.chdir(current_path)
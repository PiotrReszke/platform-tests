#!/bin/bash

PROJECT_DIR=`find . -type d -name project`
if [ "$PROJECT_DIR" = "" ]; then
    PROJECT_DIR="."
fi

source ~/virtualenvs/pyvenv_api_tests/bin/activate
cd $PROJECT_DIR
python3 run_tests.py "$@"
deactivate
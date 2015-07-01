#!/bin/bash

source ~/virtualenvs/pyvenv_api_tests/bin/activate
python3 run_tests.py "$@"
deactivate
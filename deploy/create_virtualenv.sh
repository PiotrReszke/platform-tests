#!/bin/bash

pyvenv-3.4 --without-pip ~/virtualenvs/pyvenv_api_tests &&
source ~/virtualenvs/pyvenv_api_tests/bin/activate &&
curl https://bootstrap.pypa.io/get-pip.py | python &&
~/virtualenvs/pyvenv_api_tests/bin/pip install -r requirements.txt &&
deactivate


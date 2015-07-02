#!/bin/bash

REQUIREMENTS=`find . -name requirements.txt`
PYVENV=~/virtualenvs/pyvenv_api_tests

pyvenv-3.4 --without-pip $PYVENV &&
source $PYVENV/bin/activate &&
curl https://bootstrap.pypa.io/get-pip.py | python &&
$PYVENV/bin/pip install -r $REQUIREMENTS &&
deactivate


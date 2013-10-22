#!/bin/bash

export PYTHONPATH=./src/:/lib/xively_python-0.1.0_rc2-py3.3.egg:$PYTHONPATH
export HTTP_PROXY=wwwcache.open.ac.uk:80
export HTTPS_PROXY=wwwcache.open.ac.uk:80

python3.3 -m OUSense.SenseXivelyBridge $1 $2 $3 $4

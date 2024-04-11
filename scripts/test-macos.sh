#!/usr/bin/env bash
# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -eaux
python_version=$1

VENV_DIR=./dist_venv_${python_version}

ls -l
source ./scripts/select-python.sh ${python_version}
echo $PATH

rm -rf ${VENV_DIR}
which python3
python3 --version
python3 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate
echo $PATH
which python3
python3 --version

pwd
ls -l

pip3 install *.whl
pip3 install pytest
pip3 install -r tests/requirements.txt
pip3 freeze

cd tests
pytest -v -s

rm -fr *.whl tests
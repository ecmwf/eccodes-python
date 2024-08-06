#!/usr/bin/env bash
# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -eaux
python_version=$1

ls -l
source ./scripts/select-python-linux.sh ${python_version}

echo $PATH
pwd
ls -l

pip install *.whl
pip install pytest
pip install -r tests/requirements.txt
pip freeze

ls -l $RUNNER_TEMP/venv_$version/lib/python${python_version}/site-packages/eccodes.libs/

cd tests
ECCODES_PYTHON_TRACE_LIB_SEARCH=1 pytest -v -s

rm -fr *.whl tests
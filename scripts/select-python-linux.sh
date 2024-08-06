#!/usr/bin/env bash
# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -xe
version=$1

source /opt/conda/etc/profile.d/conda.sh

CONDA_PY_ENV_DIR=$RUNNER_TEMP/venv_$version

if [ ! -d "${CONDA_PY_ENV_DIR}" ]; then
    conda create -y -p $CONDA_PY_ENV_DIR
fi

conda activate $CONDA_PY_ENV_DIR
conda install -y python=$version openldap

which python3
python3 --version

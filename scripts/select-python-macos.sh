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

P_PATH=$(brew --prefix --installed python@$version)/libexec/bin
PATH=$P_PATH:$PATH

# temporarily do not fail on unbound env vars so that this script can work outside GitHub Actions
set +u
if [ ! -z "${GITHUB_ACTION}" ]; then
    echo $P_PATH >> $GITHUB_PATH
fi
set -u

echo Python version $1 at $P_PATH

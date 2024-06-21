#!/usr/bin/env bash
# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -eaux
rm -f versions

GIT_ECBUILD=https://github.com/ecmwf/ecbuild.git
ECBUILD_VERSION=master

GIT_ECCODES=https://github.com/ecmwf/eccodes.git
ECCODES_VERSION=2.33.2
ECCODES_EXTRA_CMAKE_OPTIONS="-DENABLE_PNG=ON -DENABLE_JPG=ON -DENABLE_NETCDF=0 -DENABLE_EXAMPLES=0"

GIT_AEC=https://github.com/MathisRosenhauer/libaec.git
AEC_VERSION=master

rm -fr src build build-binaries

git clone --branch $ECBUILD_VERSION --depth=1 $GIT_ECBUILD src/ecbuild
git clone --branch $ECCODES_VERSION --depth=1 $GIT_ECCODES src/eccodes

mkdir -p build-binaries/eccodes

TOPDIR=$(/bin/pwd)

echo "================================================================================"
env | sort
echo "================================================================================"

#!/usr/bin/env bash
# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -eaux
uname -a

# HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1
HOMEBREW_NO_INSTALL_CLEANUP=1

arch=$(arch)
[[ $arch == "i386" ]] && arch="x86_64" # GitHub Actions on macOS declare i386

ARCH="arch -$arch"

source scripts/common.sh


#$ARCH brew install cmake ninja pkg-config automake
#$ARCH brew install cmake ninja netcdf libaec


for p in netcdf
do
    v=$(brew info $p | grep Cellar | awk '{print $1;}' | awk -F/ '{print $NF;}')
    echo "brew $p $v" >> versions
done

# Build eccodes

cd $TOPDIR/build-binaries/eccodes

# We disable JASPER because of a linking issue. JPEG support comes from
# other librarues
$ARCH $TOPDIR/src/ecbuild/bin/ecbuild \
    $TOPDIR/src/eccodes \
    -GNinja \
    -DCMAKE_OSX_ARCHITECTURES=$arch \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DENABLE_PYTHON=0 \
    -DENABLE_FORTRAN=0 \
    -DENABLE_BUILD_TOOLS=0 \
    -DENABLE_JPG_LIBJASPER=0 \
    -DENABLE_MEMFS=1 \
    -DENABLE_INSTALL_ECCODES_DEFINITIONS=0 \
    -DENABLE_INSTALL_ECCODES_SAMPLES=0 \
    -DCMAKE_INSTALL_PREFIX=$TOPDIR/install \
    -DCMAKE_INSTALL_RPATH=$TOPDIR/install/lib $ECCODES_EXTRA_CMAKE_OPTIONS

cd $TOPDIR
$ARCH cmake --build build-binaries/eccodes --target install


# Create wheel
rm -fr dist wheelhouse


# echo "================================================================================"
# for n in install/lib/*.dylib
# do
#     echo $n
#     ./scripts/libs-macos.py $n
# done
# echo "================================================================================"

strip -S install/lib/*.dylib

./scripts/versions.sh > gribapi/binary-versions.txt

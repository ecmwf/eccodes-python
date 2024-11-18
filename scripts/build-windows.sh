
#!/usr/bin/env bash
# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -eaux

source scripts/common.sh

here=$(pwd)
cd $VCPKG_INSTALLATION_ROOT
url=$(git remote -v | head -1 | awk '{print $2;}')
sha1=$(git rev-parse HEAD)
cd $here

echo git $url $sha1 > versions

# the results of the following suggested that pkg-config.exe is not installed on the latest
# Windows runner
#find /c/ -name pkg-config.exe
#exit 1

# if [[ $WINARCH == "x64" ]]; then
#     PKG_CONFIG_EXECUTABLE=/c/rtools43/mingw64/bin/pkg-config.exe
# else
#     PKG_CONFIG_EXECUTABLE=/c/rtools43/mingw32/bin/pkg-config.exe
# fi

vcpkg install pkgconf

for p in libpng
do
    vcpkg install $p:$WINARCH-windows
    n=$(echo $p | sed 's/\[.*//')
    v=$(vcpkg list $n | awk '{print $2;}')
    echo "vcpkg $n $v" >> versions
done

echo =================================================================
find $VCPKG_INSTALLATION_ROOT -type f -name png.h -print
echo =================================================================


pip install ninja wheel dll-diagnostics

echo "pip $(pip freeze | grep dll-diagnostics | sed 's/==/ /')" >> versions

# Build libaec
git clone $GIT_AEC src/aec
cd src/aec
git checkout $AEC_VERSION
cd $TOPDIR
mkdir -p build-binaries/aec
cd build-binaries/aec

cmake  \
    $TOPDIR/src/aec -G"NMake Makefiles" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=$TOPDIR/install \
    -DCMAKE_TOOLCHAIN_FILE=/c/vcpkg/scripts/buildsystems/vcpkg.cmake \
    -DCMAKE_C_COMPILER=cl.exe

cd $TOPDIR
cmake --build build-binaries/aec --target install



# Build eccodes

cd $TOPDIR/build-binaries/eccodes

$TOPDIR/src/ecbuild/bin/ecbuild \
    $TOPDIR/src/eccodes \
    -G"NMake Makefiles" \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DENABLE_PYTHON=0 \
    -DENABLE_FORTRAN=0 \
    -DENABLE_BUILD_TOOLS=0 \
    -DENABLE_MEMFS=1 \
    -DENABLE_INSTALL_ECCODES_DEFINITIONS=0 \
    -DENABLE_INSTALL_ECCODES_SAMPLES=0 \
    -DCMAKE_INSTALL_PREFIX=$TOPDIR/install \
    -DCMAKE_TOOLCHAIN_FILE=/c/vcpkg/scripts/buildsystems/vcpkg.cmake \
    -DCMAKE_C_COMPILER=cl.exe $ECCODES_COMMON_CMAKE_OPTIONS 

    # -DPKG_CONFIG_EXECUTABLE=$PKG_CONFIG_EXECUTABLE

cd $TOPDIR
cmake --build build-binaries/eccodes --target install


# Create wheel

rm -fr dist wheelhouse eccodes/share
pip install -r scripts/requirements.txt
find eccodes -name '*.dll' > libs
cat libs
python ./scripts/copy-licences.py libs

mkdir -p install/include

./scripts/versions.sh > eccodes/versions.txt

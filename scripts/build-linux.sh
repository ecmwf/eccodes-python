#!/usr/bin/env bash
# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
# (rm -fr build-other/netcdf/; cd src/netcdf/; git checkout -- .; git clean -f .)
set -eaux

# ensure the cleanup task can delete our workspace
umask 0000
chmod -R a+w .

pwd

GIT_OPENJPEG=https://github.com/uclouvain/openjpeg
OPENJPEG_VERSION=v2.5.2

# To allow the manylinux image to continue to use yum afer EOL. See, for example:
#   https://github.com/zanmato1984/arrow/commit/1fe15e06fac23983e5f890c2d749d9ccecd2ca15
#   https://github.com/apache/arrow/issues/43119
#sudo sed -i s/mirror.centos.org/vault.centos.org/g /etc/yum.repos.d/*.repo
#sudo sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/*.repo
#sudo sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/*.repo

source scripts/common.sh

for p in libaec-devel libpng-devel gobject-introspection-devel
do
    sudo yum install -y $p
    # There may be a better way
    sudo yum install $p 2>&1 > tmp
    cat tmp
    v=$(grep 'already installed' < tmp | awk '{print $2;}' | sed 's/\\d://')
    echo "yum $p $v" >> versions
done


sudo yum install -y flex bison

sudo ln -sf /opt/python/cp310-cp310/bin/python /usr/local/bin/python3
sudo ln -sf /opt/python/cp310-cp310/bin/python3-config /usr/local/bin/python3-config
sudo ln -sf /opt/python/cp310-cp310/bin/pip /usr/local/bin/pip3

sudo pip3 install ninja auditwheel meson 'setuptools>=72.1.0'

sudo ln -sf /opt/python/cp310-cp310/bin/meson /usr/local/bin/meson
sudo ln -sf /opt/python/cp310-cp310/bin/ninja /usr/local/bin/ninja

PKG_CONFIG_PATH=/usr/lib64/pkgconfig:/usr/lib/pkgconfig:$PKG_CONFIG_PATH
PKG_CONFIG_PATH=$TOPDIR/install/lib/pkgconfig:$TOPDIR/install/lib64/pkgconfig:$PKG_CONFIG_PATH
LD_LIBRARY_PATH=$TOPDIR/install/lib:$TOPDIR/install/lib64:$LD_LIBRARY_PATH

# Build openjpeg
# - because the one supplied with 'yum' is built with fast-math, which interferes with Python

[[ -d src/openjpeg ]] || git clone --branch $OPENJPEG_VERSION --depth=1 $GIT_OPENJPEG src/openjpeg

mkdir -p $TOPDIR/build-binaries/openjpeg
cd $TOPDIR/build-binaries/openjpeg

cmake \
    $TOPDIR/src/openjpeg/ \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_INSTALL_PREFIX=$TOPDIR/install   

cd $TOPDIR
cmake --build build-binaries/openjpeg --target install

# Build eccodes

cd $TOPDIR/build-binaries/eccodes

$TOPDIR/src/ecbuild/bin/ecbuild \
    $TOPDIR/src/eccodes \
    -GNinja \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DENABLE_PYTHON=0 \
    -DENABLE_BUILD_TOOLS=0 \
    -DENABLE_ECCODES_THREADS=1 \
    -DENABLE_JPG=1 \
    -DENABLE_JPG_LIBJASPER=0 \
    -DENABLE_JPG_LIBOPENJPEG=1 \
    -DOPENJPEG_DIR=$TOPDIR/install \
    -DENABLE_MEMFS=1 \
    -DENABLE_INSTALL_ECCODES_DEFINITIONS=0 \
    -DENABLE_INSTALL_ECCODES_SAMPLES=0 \
    -DCMAKE_INSTALL_PREFIX=$TOPDIR/install $ECCODES_COMMON_CMAKE_OPTIONS

cd $TOPDIR
cmake --build build-binaries/eccodes --target install



# Create wheel

mkdir -p install/lib/
cp install/lib64/*.so install/lib/
strip --strip-debug install/lib/*.so

./scripts/versions.sh > eccodes/versions.txt

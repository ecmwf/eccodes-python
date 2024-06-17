#!/usr/bin/env bash
# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -eaux

# ensure the cleanup task can delete our workspace
umask 0000
chmod -R a+w .

version=$(echo $1| sed 's/\.//')

TOPDIR=$(/bin/pwd)

LD_LIBRARY_PATH=$TOPDIR/install/lib:$TOPDIR/install/lib64:$LD_LIBRARY_PATH

rm -fr dist wheelhouse
/opt/python/cp${version}-cp${version}*/bin/python3 setup.py --binary-wheel bdist_wheel

# Do it twice to get the list of libraries

auditwheel repair dist/*.whl
unzip -l wheelhouse/*.whl
unzip -l wheelhouse/*.whl | grep 'eccodes.libs/' > libs
#IR pip3 install -r tools/requirements.txt

#IR python3 ./tools/copy-licences.py libs

rm -fr dist wheelhouse
/opt/python/cp${version}-cp${version}*/bin/python3 setup.py --binary-wheel bdist_wheel
auditwheel repair dist/*.whl
rm -fr dist

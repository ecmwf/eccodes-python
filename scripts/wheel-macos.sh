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

arch=$(arch)
[[ $arch == "i386" ]] && arch="x86_64" # GitHub Actions on macOS declare i386

ARCH="arch -$arch"

diet() {

    if [[ $arch == "x86_64" ]]; then
        return
    fi

    # Remove the architectures we don't need

    echo =================================================================
    pwd
    cd dist
    pwd
    name=$(ls -1 *.whl)
    echo $name
    unzip *.whl
    ls -l
    cd eccodes
    ls -l
    so=$(ls -1 *.so)
    echo "$so"

    lipo -info $so
    lipo -thin $arch $so -output $so.$arch
    mv $so.$arch $so
    lipo -info $so
    cd ..
    pwd
    zip -r $name eccodes
    cd ..

    echo =================================================================
    pwd

    ls -l dist
}

# version=$(echo $1| sed 's/\.//')
env | sort

source scripts/select-python-macos.sh $python_version


pip3 list
brew list

# set up virtualenv
$ARCH python -m venv ./dist_venv_${python_version}
source ./dist_venv_${python_version}/bin/activate

pip list
brew list

pip3 install wheel delocate setuptools pytest

rm -fr dist wheelhouse tmp
$ARCH python setup.py --binary-wheel bdist_wheel

#IR diet

name=$(ls -1 dist/*.whl)
newname=$(echo $name | sed "s/_universal2/_${arch}/")
echo $name $newname

# Do it twice to get the list of libraries
$ARCH delocate-wheel -w wheelhouse dist/*.whl
unzip -l wheelhouse/*.whl | grep 'dylib' >libs
pip3 install -r scripts/requirements.txt
python ./scripts/copy-licences.py libs

DISTUTILS_DEBUG=1

rm -fr dist wheelhouse
$ARCH python setup.py --binary-wheel bdist_wheel # --plat-name $arch
#IR diet

# mv dist/$name $newname
# find dist/*.dist-info -print

$ARCH delocate-wheel -w wheelhouse dist/*.whl

# test the wheel
pip install --force-reinstall wheelhouse/*.whl
cd tests
pytest
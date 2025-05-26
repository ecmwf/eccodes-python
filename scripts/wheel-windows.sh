#!/usr/bin/env bash
# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -eaux


pip install wheel setuptools

rm -fr dist wheelhouse ecmwflibs.egg-info build
python setup_windows.py --binary-wheel bdist_wheel
mv dist wheelhouse

ls -l wheelhouse

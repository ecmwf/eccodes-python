#!/usr/bin/env bash
# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -xe
version=$1

brew install python@$1

echo /opt/homebrew/opt/python@$version/libexec/bin >> $GITHUB_PATH

ls -l /opt/homebrew/opt/python@$version/libexec/bin

# Looks like python3 is not a symlink to python in 3.11

if [[ ! -f /opt/homebrew/opt/python@$version/libexec/bin/python3 ]]
then
    ln -s /opt/homebrew/opt/python@$version/libexec/bin/python /opt/homebrew/opt/python@$version/libexec/bin/python3
fi

if [[ ! -f /opt/homebrew/opt/python@$version/libexec/bin/pip3 ]]
then
    ln -s /opt/homebrew/opt/python@$version/libexec/bin/pip /opt/homebrew/opt/python@$version/libexec/bin/pip3
fi

ls -l

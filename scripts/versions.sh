#!/usr/bin/env bash
# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

set -eaux
cat versions
cd src

for n in *
do
  cd $n
  url=$(git remote -v | head -1 | awk '{print $2;}')
  sha1=$(git rev-parse HEAD)
  echo git $url $sha1
  cd ..
done

cd ..

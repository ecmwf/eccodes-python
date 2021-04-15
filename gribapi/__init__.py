#
# (C) Copyright 2017- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
#
#

from .gribapi import *  # noqa
from .gribapi import __version__, lib

# The minimum recommended version for the ecCodes package
min_recommended_version_str = "2.21.0"
min_recommended_version_int = 22100

if lib.grib_get_api_version() < min_recommended_version_int:
    print(
        "Warning: ecCodes %s or higher is recommended. You are running version %s"
        % (min_recommended_version_str, __version__)
    )

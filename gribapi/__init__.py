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
from .gribapi import __version__
from .gribapi import bindings_version

# The minimum required version for the ecCodes package
min_reqd_version_str = "2.17.0"
min_reqd_version_int = 21700

if lib.grib_get_api_version() < min_reqd_version_int:
    print(
        "Warning: ecCodes %s or higher is recommended. You are running version %s"
        % (min_reqd_version_str, __version__)
    )

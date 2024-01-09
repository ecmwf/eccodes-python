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

# Authors:
#   Alessandro Amici - B-Open - https://bopen.eu
#   Shahram Najm - ECMWF - https://www.ecmwf.int
#

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import pkgutil

import cffi

__version__ = "1.7.0"

LOG = logging.getLogger(__name__)

try:
    import ecmwflibs as findlibs
except ImportError:
    import findlibs

library_path = findlibs.find("eccodes")
if library_path is None:
    raise RuntimeError("Cannot find the ecCodes library")

# default encoding for ecCodes strings
ENC = "ascii"

ffi = cffi.FFI()
CDEF = pkgutil.get_data(__name__, "grib_api.h")
CDEF += pkgutil.get_data(__name__, "eccodes.h")
ffi.cdef(CDEF.decode("utf-8").replace("\r", "\n"))


lib = ffi.dlopen(library_path)

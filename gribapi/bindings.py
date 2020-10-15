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
#

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import pkgutil
import os

import cffi

__version__ = "1.0.1"

LOG = logging.getLogger(__name__)

try:
    from ._bindings import ffi, lib
except ModuleNotFoundError:
    ffi = cffi.FFI()
    ffi.cdef(
        pkgutil.get_data(__name__, "grib_api.h").decode("utf-8")
        + pkgutil.get_data(__name__, "eccodes.h").decode("utf-8")
    )

    LIBNAMES = ["eccodes", "libeccodes.so", "libeccodes"]

    try:
        import ecmwflibs

        LIBNAMES.insert(0, ecmwflibs.find("eccodes"))
    except Exception:
        pass

    if os.environ.get("ECCODES_DIR"):
        eccdir = os.environ["ECCODES_DIR"]
        LIBNAMES.insert(0, os.path.join(eccdir, "lib/libeccodes.so"))
        LIBNAMES.insert(0, os.path.join(eccdir, "lib64/libeccodes.so"))

    for libname in LIBNAMES:
        try:
            lib = ffi.dlopen(libname)
            LOG.info("ecCodes library found using name '%s'.", libname)
            break
        except OSError:
            # lazy exception
            lib = None
            LOG.info("ecCodes library not found using name '%s'.", libname)
            raise RuntimeError(f"ecCodes library not found using {LIBNAMES}")

# default encoding for ecCodes strings
ENC = "ascii"

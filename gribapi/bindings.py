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


__version__ = "1.3.1"

LOG = logging.getLogger(__name__)

try:
    import ecmwflibs as findlibs
except ImportError:
    import findlibs

lib = findlibs.find("eccodes")
if lib is None:
    raise RuntimeError("Cannot find eccodes library")

# default encoding for ecCodes strings
ENC = "ascii"

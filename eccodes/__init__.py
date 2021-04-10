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
from __future__ import absolute_import

import sys

from .eccodes import *
from .eccodes import __version__, bindings_version

if sys.version_info >= (2, 6):
    from .high_level.bufr import BufrFile, BufrMessage
    from .high_level.gribfile import GribFile
    from .high_level.gribindex import GribIndex
    from .high_level.gribmessage import GribMessage

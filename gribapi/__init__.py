#
# Copyright 2017-2020 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

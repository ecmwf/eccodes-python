from .gribapi import *  # noqa
from .gribapi import __version__
from .gribapi import bindings_version

# The minimum required version for the ecCodes package
min_reqd_version_str = "2.16.0"
min_reqd_version_int = 21600

if lib.grib_get_api_version() < min_reqd_version_int:
    print(
        "Warning: ecCodes %s or higher is recommended. You are running version %s"
        % (min_reqd_version_str, __version__)
    )

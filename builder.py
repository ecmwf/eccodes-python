import logging
import sys

import cffi

ffibuilder = cffi.FFI()
ffibuilder.set_source(
    "gribapi._bindings",
    "#include <eccodes.h>",
    libraries=["eccodes"],
)
ffibuilder.cdef(open("gribapi/grib_api.h").read() + open("gribapi/eccodes.h").read())

if __name__ == "__main__":
    try:
        ffibuilder.compile(verbose=True)
    except Exception:
        logging.exception("can't compile ecCodes bindings")
        sys.exit(1)

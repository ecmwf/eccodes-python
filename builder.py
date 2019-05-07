import logging

import cffi

ffibuilder = cffi.FFI()
ffibuilder.set_source(
    "gribapi._bindings",
    '#include "grib_api_internal.h"\n#include <eccodes.h>',
    libraries=["eccodes"],
)
ffibuilder.cdef(
    open("gribapi/grib_api.h").read() +
    open("gribapi/grib_api_prototypes.h").read() +
    open("gribapi/eccodes.h").read()
)

if __name__ == "__main__":
    try:
        ffibuilder.compile(verbose=True)
    except Exception:
        logging.exception("can't compile ecCodes bindings")
